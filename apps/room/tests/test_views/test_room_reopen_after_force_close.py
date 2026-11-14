from collections.abc import Callable

import pytest

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestReopenAfterForceClose:
    def test_reverting_restores_exactly_the_force_settled_debts(
        self, post_status: Callable, room_with_settled_and_open_debt: Room
    ) -> None:
        room = room_with_settled_and_open_debt
        post_status(room, status=Room.StatusChoices.CLOSED, force_close="true")

        post_status(room, status=Room.StatusChoices.OPEN, revert_force_settled="true")

        room.refresh_from_db()
        assert room.status == Room.StatusChoices.OPEN
        # Two expenses of 13, one honestly settled: exactly 13 stays owed.
        open_debt = Debt.objects.get(room=room, settled=False)
        assert open_debt.value == 13
        assert open_debt.settled_at is None
        assert Debt.objects.get(room=room, settled=True).value == 13
        assert not Debt.objects.filter(room=room, force_settled_at__isnull=False).exists()

    def test_keeping_the_debts_settled_only_drops_the_marker(
        self, post_status: Callable, room_with_settled_and_open_debt: Room
    ) -> None:
        room = room_with_settled_and_open_debt
        post_status(room, status=Room.StatusChoices.CLOSED, force_close="true")

        post_status(room, status=Room.StatusChoices.OPEN)

        assert Debt.objects.filter(room=room, settled=True).count() == 2
        assert not Debt.objects.filter(room=room, force_settled_at__isnull=False).exists()

    def test_the_revert_flag_does_nothing_without_force_settled_debts(
        self, post_status: Callable, closed_room: Room, user: User, guest_user: User
    ) -> None:
        create_parent_transaction_with_optimisation(room=closed_room, paid_by=user, paid_for_tuple=(guest_user,))
        Debt.objects.filter(room=closed_room).update(settled=True)

        post_status(closed_room, status=Room.StatusChoices.OPEN, revert_force_settled="true")

        assert Debt.objects.filter(room=closed_room, settled=True).count() == 1
        assert not Debt.objects.filter(room=closed_room, settled=False).exists()

    def test_the_dialog_is_offered_only_for_a_force_closed_room(
        self, post_status: Callable, room_with_settled_and_open_debt: Room, closed_room: Room
    ) -> None:
        forced, _ = post_status(room_with_settled_and_open_debt, status=Room.StatusChoices.CLOSED, force_close="true")
        plain, _ = post_status(closed_room, status=Room.StatusChoices.CLOSED)

        assert "reopen-room-revert-button" in forced.content.decode()
        assert "reopen-room-dialog" not in plain.content.decode()
