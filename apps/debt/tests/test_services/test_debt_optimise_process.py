from decimal import Decimal
from unittest import mock

import pytest
from django.db import transaction

from apps.account.models import User
from apps.debt.models import Debt
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room
from apps.transaction.models import ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory


@pytest.mark.django_db
class TestProcess:
    def test_a_failing_rebuild_keeps_the_previous_debts(self, room: Room, user: User, guest_user: User) -> None:
        parent = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
        ChildTransaction.objects.create(parent_transaction=parent, paid_for=guest_user, value=Decimal("10.00"))
        DebtOptimiseService.process(room.id)
        assert Debt.objects.filter(room=room, settled=False).count() == 1

        with (
            mock.patch.object(Debt.objects, "bulk_create", side_effect=RuntimeError("boom")),
            pytest.raises(RuntimeError),
            transaction.atomic(),
        ):
            DebtOptimiseService.process(room.id)

        assert Debt.objects.filter(room=room, settled=False).count() == 1

    def test_the_rebuild_locks_the_room_row(self, room: Room) -> None:
        with mock.patch("apps.debt.services.debt_optimise_service.Room.objects") as room_objects:
            DebtOptimiseService.process(room.id)

        room_objects.select_for_update.assert_called_once_with()
        room_objects.select_for_update.return_value.get.assert_called_once_with(pk=room.id)

    def test_rebuilding_twice_does_not_duplicate_debts(self, room: Room, user: User, guest_user: User) -> None:
        parent = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
        ChildTransaction.objects.create(parent_transaction=parent, paid_for=guest_user, value=Decimal("10.00"))

        DebtOptimiseService.process(room.id)
        DebtOptimiseService.process(room.id)

        assert list(Debt.objects.filter(room=room).values_list("debitor_id", "creditor_id", "value")) == [
            (guest_user.id, user.id, Decimal("10.00"))
        ]
