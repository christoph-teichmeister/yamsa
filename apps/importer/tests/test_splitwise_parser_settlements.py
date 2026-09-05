from decimal import Decimal

import pytest

from apps.importer.parsers.splitwise import SplitwiseCsvParser
from apps.importer.tests.factories import build_file_like


def parse(rows, header=None):
    kwargs = {"header": header} if header else {}
    return SplitwiseCsvParser().parse(build_file_like(rows, **kwargs))


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
