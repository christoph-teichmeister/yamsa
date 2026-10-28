from decimal import Decimal

import pytest

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.models import Room
from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.tests.test_forms.conftest import create_data

pytestmark = pytest.mark.django_db


class TestCreateFormDebtors:
    def test_a_debtor_outside_the_room_is_rejected(self, room: Room, user: User) -> None:
        outsider = UserFactory()
        form = TransactionCreateForm(
            data=create_data(room, user, [user.id, outsider.id], ["5.00", "5.00"], "10.00"), room=room
        )

        assert not form.is_valid()
        assert "paid_for" in form.errors

    def test_arrays_of_different_length_are_rejected_instead_of_dropping_shares(
        self, room: Room, user: User, guest_user: User
    ) -> None:
        form = TransactionCreateForm(
            data=create_data(room, user, [user.id, guest_user.id], ["5.00"], "10.00"), room=room
        )

        assert not form.is_valid()
        assert "value" in form.errors

    def test_a_negative_share_is_rejected(self, room: Room, user: User, guest_user: User) -> None:
        form = TransactionCreateForm(
            data=create_data(room, user, [user.id, guest_user.id], ["15.00", "-5.00"], "10.00"), room=room
        )

        assert not form.is_valid()
        assert "value" in form.errors

    def test_all_shares_zero_is_rejected(self, room: Room, user: User, guest_user: User) -> None:
        form = TransactionCreateForm(
            data=create_data(room, user, [user.id, guest_user.id], ["0.00", "0.00"], "10.00"), room=room
        )
        # The total was typed, but the shares were not: they stay zero only when it matches the reference.
        form.data["total_value"] = "0.00"
        form.data["reference_total_value"] = "0.00"

        assert not form.is_valid()
        assert "value" in form.errors

    def test_a_zero_share_is_not_stored(self, room: Room, user: User, guest_user: User) -> None:
        form = TransactionCreateForm(
            data=create_data(room, user, [user.id, guest_user.id], ["10.00", "0.00"], "10.00"), room=room
        )

        assert form.is_valid(), form.errors
        parent = form.save()

        assert list(parent.child_transactions.values_list("paid_for_id", "value")) == [(user.id, Decimal("10.00"))]
        assert parent.value == Decimal("10.00")
