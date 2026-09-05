from decimal import Decimal

import pytest

from apps.importer.parsers.base import ImportParseError
from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


class TestSplitwiseCsvParserHappyPath:
    def test_reads_people_from_header(self):
        result = parse(["2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97"])

        assert result.people == ("Kilian Karaus", "Elisabeth")

    def test_splits_a_shared_expense_into_shares(self):
        result = parse(["2023-02-28,Cambio 04.02. ikea,Möbel,21.80,EUR,-10.90,10.90"])

        transaction = result.transactions[0]
        assert transaction.payer == "Elisabeth"
        assert transaction.total == Decimal("21.80")
        assert {share.person: share.value for share in transaction.shares} == {
            "Elisabeth": Decimal("10.90"),
            "Kilian Karaus": Decimal("10.90"),
        }

    def test_payer_with_zero_share_gets_no_child(self):
        result = parse(["2023-02-28,Cambio 24.02.23,Allgemein,25.20,EUR,-25.20,25.20"])

        transaction = result.transactions[0]
        assert transaction.payer == "Elisabeth"
        assert [(share.person, share.value) for share in transaction.shares] == [("Kilian Karaus", Decimal("25.20"))]

    def test_uninvolved_person_gets_no_child(self):
        header = "Datum,Beschreibung,Kategorie,Kosten,Währung,Anna,Ben,Cleo"
        result = parse(["2023-03-06,Kaffee,Allgemein,10.00,EUR,5.00,-5.00,0.00"], header=header)

        transaction = result.transactions[0]
        assert {share.person for share in transaction.shares} == {"Anna", "Ben"}

    def test_long_description_is_truncated_and_kept_in_notes(self):
        description = "D" * 80
        result = parse([f"2023-03-06,{description},Allgemein,10.00,EUR,5.00,-5.00"])

        transaction = result.transactions[0]
        assert len(transaction.description) == 50
        assert transaction.further_notes == description

    def test_short_description_leaves_notes_empty(self):
        result = parse(["2023-03-06,Ikea,Allgemein,10.00,EUR,5.00,-5.00"])

        assert result.transactions[0].further_notes == ""

    def test_collects_currency_codes_most_frequent_first(self):
        result = parse(
            [
                "2023-03-06,A,Allgemein,10.00,EUR,5.00,-5.00",
                "2023-03-07,B,Allgemein,10.00,EUR,5.00,-5.00",
                "2023-03-08,C,Allgemein,10.00,GBP,5.00,-5.00",
            ]
        )

        assert result.currency_codes == ["EUR", "GBP"]


class TestSplitwiseCsvParserSkippedRows:
    @pytest.mark.parametrize(
        ("row", "expected_fragment"),
        [
            ("2026-09-05,Gesamtbilanz, , ,EUR,36.39,-36.39", "cost"),
            ("2023-03-06,Krumm,Allgemein,10.00,EUR,5.00,-4.00", "cancel out"),
            ("2023-03-06,Kein Zahler,Allgemein,10.00,EUR,0.00,0.00", "No payer"),
            ("2023-03-06,Nullbetrag,Allgemein,0.00,EUR,0.00,0.00", "zero"),
            ("kein-datum,Datumsfehler,Allgemein,10.00,EUR,5.00,-5.00", "date"),
            ("2023-03-06,Kostenfehler,Allgemein,abc,EUR,5.00,-5.00", "cost"),
        ],
    )
    def test_row_is_skipped_with_reason(self, row, expected_fragment):
        result = parse([row])

        assert result.transactions == ()
        assert len(result.skipped_rows) == 1
        assert expected_fragment.lower() in result.skipped_rows[0].reason.lower()

    def test_row_with_two_payers_is_skipped(self):
        header = "Datum,Beschreibung,Kategorie,Kosten,Währung,Anna,Ben,Cleo"
        result = parse(["2023-03-06,Zwei Zahler,Allgemein,15.00,EUR,10.00,5.00,-15.00"], header=header)

        assert result.transactions == ()
        assert "more than one payer" in result.skipped_rows[0].reason.lower()

    def test_blank_lines_are_ignored_without_being_reported(self):
        result = parse(["", "   ", "2023-03-06,Ikea,Allgemein,10.00,EUR,5.00,-5.00"])

        assert len(result.transactions) == 1
        assert result.skipped_rows == ()

    def test_skipped_row_keeps_its_spreadsheet_row_number(self):
        result = parse(
            [
                "2023-03-06,Ikea,Allgemein,10.00,EUR,5.00,-5.00",
                "2023-03-07,Gesamtbilanz,,,EUR,5.00,-5.00",
            ]
        )

        assert result.skipped_rows[0].row_number == 3


class TestSplitwiseCsvParserSettlements:
    @pytest.mark.parametrize("label", ["Zahlung", "payment", "  ZAHLUNG  "])
    def test_payment_row_becomes_a_settlement(self, label):
        result = parse([f"2024-10-04,Zahlung,{label},276.16,EUR,276.16,-276.16"])

        assert result.transactions == ()
        settlement = result.settlements[0]
        # The person who transferred the money owed it.
        assert settlement.debitor == "Kilian Karaus"
        assert settlement.creditor == "Elisabeth"
        assert settlement.value == Decimal("276.16")
        assert settlement.settled_at.isoformat() == "2024-10-04"

    def test_settlement_with_three_involved_columns_is_skipped(self):
        header = "Datum,Beschreibung,Kategorie,Kosten,Währung,Anna,Ben,Cleo"
        result = parse(["2024-10-04,Zahlung,Zahlung,10.00,EUR,10.00,-4.00,-6.00"], header=header)

        assert result.settlements == ()
        assert "exactly one payer" in result.skipped_rows[0].reason

    def test_settlement_is_not_counted_as_a_category(self):
        result = parse(["2024-10-04,Zahlung,Zahlung,10.00,EUR,10.00,-10.00"])

        assert result.categories == ()


class TestSplitwiseCsvParserCategories:
    @pytest.mark.parametrize(
        ("label", "expected_slug"),
        [
            ("Allgemein", "misc"),
            ("Lebensmittel", "groceries"),
            ("Restaurant", "restaurants-and-bars"),
            ("Treibstoff", "transport"),
            ("Möbel", "household"),
            ("Zuhause - Sonstiges", "household"),
            ("Kino", "activities"),
            ("Voellig Unbekannt", "misc"),
        ],
    )
    def test_category_label_maps_to_slug(self, label, expected_slug):
        assert SplitwiseCsvParser.map_category_slug(label) == expected_slug

    def test_unknown_label_gets_the_fallback_emoji(self):
        assert SplitwiseCsvParser.suggest_emoji("Voellig Unbekannt") == "🏷️"

    def test_known_label_gets_a_specific_emoji(self):
        assert SplitwiseCsvParser.suggest_emoji("Treibstoff") == "⛽"

    def test_categories_are_counted_and_sorted_by_frequency(self):
        result = parse(
            [
                "2023-03-06,A,Restaurant,10.00,EUR,5.00,-5.00",
                "2023-03-07,B,Möbel,10.00,EUR,5.00,-5.00",
                "2023-03-08,C,Restaurant,10.00,EUR,5.00,-5.00",
            ]
        )

        assert [(entry.label, entry.transaction_count) for entry in result.categories] == [
            ("Restaurant", 2),
            ("Möbel", 1),
        ]


class TestSplitwiseCsvParserRejectsFiles:
    def test_empty_file_is_rejected(self):
        with pytest.raises(ImportParseError):
            SplitwiseCsvParser().parse(build_file_like([], header=""))

    def test_header_without_person_columns_is_rejected(self):
        with pytest.raises(ImportParseError, match="person columns"):
            parse(["2023-03-06,A,Allgemein,10.00,EUR"], header="Datum,Beschreibung,Kategorie,Kosten,Währung")

    def test_non_utf8_file_is_rejected(self):
        import io

        with pytest.raises(ImportParseError, match="UTF-8"):
            SplitwiseCsvParser().parse(io.BytesIO(b"\xff\xfe\x00invalid"))


class TestSplitwiseCsvParserSerialisation:
    def test_parsed_import_survives_a_json_round_trip(self):
        import json

        result = parse(
            [
                "2023-03-06,Ikea,Möbel,72.97,EUR,72.97,-72.97",
                "2024-10-04,Zahlung,Zahlung,10.00,EUR,10.00,-10.00",
                "2026-09-05,Gesamtbilanz,,,EUR,5.00,-5.00",
            ]
        )

        from apps.importer.dataclasses import ParsedImport

        restored = ParsedImport.from_payload(json.loads(json.dumps(result.as_payload())))

        assert restored == result
