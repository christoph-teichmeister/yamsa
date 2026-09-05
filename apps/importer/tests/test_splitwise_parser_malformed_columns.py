from decimal import Decimal

from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


class TestSplitwiseCsvParserMalformedColumns:
    def test_blank_header_column_does_not_shift_later_values(self):
        # The blank column sits between the two people; reading positionally by filtered index
        # would attribute Bob's value to the empty column.
        header = "Datum,Beschreibung,Kategorie,Kosten,Währung,Anna,,Bob"
        result = parse(["2023-03-06,Kaffee,Allgemein,10.00,EUR,5.00,,-5.00"], header=header)

        assert result.skipped_rows == ()
        transaction = result.transactions[0]
        assert transaction.payer == "Anna"
        assert {share.person: share.value for share in transaction.shares} == {
            "Anna": Decimal("5.00"),
            "Bob": Decimal("5.00"),
        }

    def test_duplicate_headings_become_distinct_people(self):
        header = "Datum,Beschreibung,Kategorie,Kosten,Währung,Anna,Anna"
        result = parse(["2023-03-06,Kaffee,Allgemein,10.00,EUR,5.00,-5.00"], header=header)

        assert result.people == ("Anna", "Anna (2)")
        transaction = result.transactions[0]
        assert transaction.payer == "Anna"
        # Both columns must survive as separate shares instead of collapsing onto one person.
        assert {share.person for share in transaction.shares} == {"Anna", "Anna (2)"}

    def test_trailing_blank_headings_are_ignored(self):
        header = "Datum,Beschreibung,Kategorie,Kosten,Währung,Anna,Bob,"
        result = parse(["2023-03-06,Kaffee,Allgemein,10.00,EUR,5.00,-5.00,"], header=header)

        assert result.people == ("Anna", "Bob")
        assert result.skipped_rows == ()
