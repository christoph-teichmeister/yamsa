from decimal import Decimal

import pytest

from apps.account.models import User
from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.mark.django_db
class TestBalancesByCurrency:
    def test_currencies_are_kept_apart(self, room: Room, user: User, guest_user: User) -> None:
        euro, forint = CurrencyFactory(), CurrencyFactory()
        for currency, amount in ((euro, Decimal("10.00")), (forint, Decimal("2500.00"))):
            parent = ParentTransactionFactory(room=room, paid_by=user, currency=currency)
            ChildTransaction.objects.create(parent_transaction=parent, paid_for=guest_user, value=amount)

        balances = DebtOptimiseService._balances_by_currency(room.id)

        assert balances[euro.id] == {user.id: Decimal("10.00"), guest_user.id: Decimal("-10.00")}
        assert balances[forint.id] == {user.id: Decimal("2500.00"), guest_user.id: Decimal("-2500.00")}

    def test_a_settled_debt_offsets_the_balance(self, room: Room, user: User, guest_user: User) -> None:
        parent = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
        ChildTransaction.objects.create(parent_transaction=parent, paid_for=guest_user, value=Decimal("10.00"))
        Debt.objects.create(
            debitor=guest_user,
            creditor=user,
            room=room,
            value=Decimal("4.00"),
            currency=room.preferred_currency,
            settled=True,
        )

        balances = DebtOptimiseService._balances_by_currency(room.id)[room.preferred_currency.id]

        assert balances == {user.id: Decimal("6.00"), guest_user.id: Decimal("-6.00")}

    def test_other_rooms_do_not_leak_in(self, room: Room, closed_room: Room, user: User, guest_user: User) -> None:
        parent = ParentTransactionFactory(room=closed_room, paid_by=user, currency=closed_room.preferred_currency)
        ChildTransaction.objects.create(parent_transaction=parent, paid_for=guest_user, value=Decimal("10.00"))

        assert dict(DebtOptimiseService._balances_by_currency(room.id)) == {}
