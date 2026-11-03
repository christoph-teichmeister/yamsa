from decimal import Decimal

import pytest

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.models import Room
from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from apps.transaction.tests.test_forms.conftest import edit_data

pytestmark = pytest.mark.django_db


class TestEditFormDebtors:
    def test_a_debtor_outside_the_room_is_rejected(self, parent_transaction: ParentTransaction, user: User) -> None:
        outsider = UserFactory()
        data = edit_data(parent_transaction, paid_for=[user.id, outsider.id], child_transaction_id=[0, 0])

        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert not form.is_valid()
        assert "paid_for" in form.errors

    def test_a_share_of_another_transaction_is_rejected(
        self, parent_transaction: ParentTransaction, room: Room, user: User
    ) -> None:
        other = ParentTransactionFactory(room=room, paid_by=user)
        foreign_share = ChildTransaction.objects.create(parent_transaction=other, paid_for=user, value=Decimal(5))
        data = edit_data(
            parent_transaction, paid_for=[user.id], value=["5.00"], child_transaction_id=[foreign_share.id]
        )

        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert not form.is_valid()
        assert "child_transaction_id" in form.errors
