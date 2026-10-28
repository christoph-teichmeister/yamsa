from decimal import Decimal

import pytest

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.models import Room
from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.test_forms.conftest import edit_data

pytestmark = pytest.mark.django_db


class TestEditFormShareRows:
    @pytest.mark.parametrize(
        "overrides",
        [
            {"value": ["10.00"]},
            {"child_transaction_id": [1]},
            {"paid_for": []},
        ],
    )
    def test_arrays_of_different_length_are_a_field_error_not_a_500(
        self, parent_transaction: ParentTransaction, overrides: dict
    ) -> None:
        form = TransactionEditForm(data=edit_data(parent_transaction, **overrides), instance=parent_transaction)

        assert not form.is_valid()
        assert form.errors

    def test_a_debtor_repeated_without_an_id_is_folded_into_the_existing_share(
        self, parent_transaction: ParentTransaction, user: User, guest_user: User
    ) -> None:
        existing = list(parent_transaction.child_transactions.order_by("id"))
        data = edit_data(
            parent_transaction,
            paid_for=[user.id, guest_user.id, user.id],
            value=["10.00", "20.00", "5.00"],
            child_transaction_id=[existing[0].id, existing[1].id, 0],
        )
        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert form.is_valid(), form.errors
        form.save()

        assert parent_transaction.child_transactions.get(paid_for=user).value == Decimal("15.00")
        assert parent_transaction.child_transactions.count() == 2

    def test_a_new_debtor_repeated_twice_becomes_one_share(
        self, parent_transaction: ParentTransaction, room: Room
    ) -> None:
        newcomer = UserFactory()
        room.users.add(newcomer)
        data = edit_data(parent_transaction)
        data["paid_for"] += [newcomer.id, newcomer.id]
        data["value"] += ["3.00", "4.00"]
        data["child_transaction_id"] += [0, 0]
        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert form.is_valid(), form.errors
        form.save()

        assert parent_transaction.child_transactions.get(paid_for=newcomer).value == Decimal("7.00")

    def test_a_negative_share_is_rejected(self, parent_transaction: ParentTransaction) -> None:
        form = TransactionEditForm(
            data=edit_data(parent_transaction, value=["30.00", "-10.00"]), instance=parent_transaction
        )

        assert not form.is_valid()
        assert "value" in form.errors

    def test_a_zero_share_removes_the_debtor_on_save(
        self, parent_transaction: ParentTransaction, user: User, guest_user: User
    ) -> None:
        data = edit_data(parent_transaction, value=["10.00", "0.00"])
        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert form.is_valid(), form.errors
        form.save()

        assert list(parent_transaction.child_transactions.values_list("paid_for_id", flat=True)) == [user.id]

    def test_all_shares_zero_is_rejected(self, parent_transaction: ParentTransaction) -> None:
        form = TransactionEditForm(data=edit_data(parent_transaction, value=["0", "0"]), instance=parent_transaction)

        assert not form.is_valid()
        assert "value" in form.errors

    def test_changing_the_total_without_debtors_names_the_debtor_field(
        self, parent_transaction: ParentTransaction
    ) -> None:
        data = edit_data(parent_transaction, paid_for=[], value=[], child_transaction_id=[], total_value="50.00")
        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert not form.is_valid()
        assert "paid_for" in form.errors
