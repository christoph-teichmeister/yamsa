from decimal import Decimal

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
