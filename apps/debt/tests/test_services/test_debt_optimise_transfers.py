from decimal import Decimal

from apps.debt.services.debt_optimise_service import DebtOptimiseService


def settled_balance(transfers: list[tuple[int, int, Decimal]]) -> dict[int, Decimal]:
    balance: dict[int, Decimal] = {}
    for debtor, creditor, amount in transfers:
        balance[debtor] = balance.get(debtor, Decimal(0)) + amount
        balance[creditor] = balance.get(creditor, Decimal(0)) - amount
    return balance


class TestTransfers:
    def test_an_already_balanced_room_needs_no_transfer(self) -> None:
        assert DebtOptimiseService._transfers({1: Decimal(0), 2: Decimal(0)}) == []

    def test_a_chain_collapses_into_one_transfer(self) -> None:
        # A owes B 10 and B owes C 10: B is square, so A pays C directly.
        assert DebtOptimiseService._transfers({1: Decimal(-10), 2: Decimal(0), 3: Decimal(10)}) == [(1, 3, Decimal(10))]

    def test_one_debtor_is_split_across_several_creditors_largest_first(self) -> None:
        transfers = DebtOptimiseService._transfers({1: Decimal(-30), 2: Decimal(10), 3: Decimal(20)})

        assert transfers == [(1, 3, Decimal(20)), (1, 2, Decimal(10))]

    def test_one_creditor_collects_from_several_debtors_largest_first(self) -> None:
        transfers = DebtOptimiseService._transfers({1: Decimal(-10), 2: Decimal(-20), 3: Decimal(30)})

        assert transfers == [(2, 3, Decimal(20)), (1, 3, Decimal(10))]

    def test_cent_remainders_are_carried_to_the_next_transfer(self) -> None:
        balances = {1: Decimal("-33.34"), 2: Decimal("-33.33"), 3: Decimal("-33.33"), 4: Decimal("100.00")}

        transfers = DebtOptimiseService._transfers(balances)

        assert [amount for _, _, amount in transfers] == [Decimal("33.34"), Decimal("33.33"), Decimal("33.33")]
        assert sum(amount for _, _, amount in transfers) == Decimal("100.00")

    def test_the_transfers_settle_every_balance_exactly(self) -> None:
        balances = {1: Decimal("-12.34"), 2: Decimal("-7.66"), 3: Decimal("5.01"), 4: Decimal("14.99")}

        result = settled_balance(DebtOptimiseService._transfers(balances))

        assert result == {person: -balance for person, balance in balances.items()}
