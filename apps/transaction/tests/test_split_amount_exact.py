from decimal import Decimal

import pytest

from apps.transaction.utils import split_amount_exact, split_total_across_paid_for


class TestSplitAmountExact:
    def test_one_hundred_across_three_gives_the_remainder_cent_to_the_first(self) -> None:
        assert split_amount_exact(Decimal("100.00"), 3) == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]

    @pytest.mark.parametrize(
        ("total", "shares"),
        [("0.01", 3), ("0.10", 3), ("100.00", 7), ("19.99", 4), ("1.00", 6), ("-10.00", 3), ("0.00", 5)],
    )
    def test_the_shares_always_sum_to_the_total(self, total: str, shares: int) -> None:
        result = split_amount_exact(Decimal(total), shares)

        assert len(result) == shares
        assert sum(result) == Decimal(total)
        assert max(result) - min(result) <= Decimal("0.01")

    def test_zero_shares_is_an_error(self) -> None:
        with pytest.raises(ValueError, match="shares must be > 0"):
            split_amount_exact(Decimal("10.00"), 0)

    def test_total_across_paid_for_needs_a_participant(self) -> None:
        with pytest.raises(ValueError, match="at least one participant"):
            split_total_across_paid_for(Decimal("10.00"), [])
