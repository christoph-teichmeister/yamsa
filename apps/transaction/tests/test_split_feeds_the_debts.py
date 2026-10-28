from decimal import Decimal

import pytest

from apps.account.models import User
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from apps.transaction.utils import split_total_across_paid_for


@pytest.mark.django_db
class TestSplitFeedsTheDebts:
    def test_the_payer_who_is_also_a_debtor_owes_nothing_to_themselves(
        self, room: Room, user: User, guest_user: User
    ) -> None:
        parent = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
        for debtor, share in zip(
            (user, guest_user), split_total_across_paid_for(Decimal("100.00"), (1, 2)), strict=True
        ):
            ChildTransaction.objects.create(parent_transaction=parent, paid_for=debtor, value=share)

        balances = DebtOptimiseService._balances_by_currency(room.id)[room.preferred_currency.id]

        assert balances == {user.id: Decimal("50.00"), guest_user.id: Decimal("-50.00")}

    def test_an_uneven_split_leaves_the_payer_and_debtors_balanced_to_the_cent(
        self, room: Room, user: User, guest_user: User
    ) -> None:
        third = User.objects.create(email="third@yamsa.local", name="Third")
        room.users.add(third)
        parent = ParentTransactionFactory(room=room, paid_by=user, currency=CurrencyFactory())
        shares = split_total_across_paid_for(Decimal("100.00"), (1, 2, 3))
        for debtor, share in zip((user, guest_user, third), shares, strict=True):
            ChildTransaction.objects.create(parent_transaction=parent, paid_for=debtor, value=share)

        balances = DebtOptimiseService._balances_by_currency(room.id)[parent.currency_id]

        assert sum(balances.values()) == Decimal("0.00")
        assert balances[user.id] == Decimal("66.66")
        assert balances[guest_user.id] == Decimal("-33.33")
        assert balances[third.id] == Decimal("-33.33")
