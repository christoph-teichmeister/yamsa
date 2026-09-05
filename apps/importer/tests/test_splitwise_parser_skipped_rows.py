import pytest

from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


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
