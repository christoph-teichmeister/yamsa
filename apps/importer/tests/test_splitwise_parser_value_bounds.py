from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


class TestSplitwiseCsvParserValueBounds:
    def test_more_than_two_decimal_places_is_skipped(self):
        result = parse(["2023-03-06,Kaffee,Allgemein,10.005,EUR,5.0025,-5.0025"])

        assert result.transactions == ()
        assert "unreadable" in result.skipped_rows[0].reason.lower()

    def test_value_beyond_the_model_limit_is_skipped(self):
        result = parse(["2023-03-06,Kaffee,Allgemein,123456789012.00,EUR,61728394506.00,-61728394506.00"])

        assert result.transactions == ()
        assert result.skipped_rows != ()

    def test_notes_are_capped_at_the_model_limit(self):
        description = "D" * 6000
        result = parse([f"2023-03-06,{description},Allgemein,10.00,EUR,5.00,-5.00"])

        assert len(result.transactions[0].further_notes) == 5000

    def test_negative_cost_reason_says_so(self):
        result = parse(["2023-03-06,Gutschrift,Allgemein,-10.00,EUR,-5.00,5.00"])

        assert "negative" in result.skipped_rows[0].reason.lower()
