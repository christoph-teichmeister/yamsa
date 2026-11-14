from collections.abc import Callable
from unittest import mock

import pytest
from django.db import DatabaseError

from apps.debt.models import Debt
from apps.debt.querysets import DebtQuerySet
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestForceCloseRecording:
    def test_only_the_force_settled_debts_are_marked(
        self, post_status: Callable, room_with_settled_and_open_debt: Room
    ) -> None:
        room = room_with_settled_and_open_debt

        post_status(room, status=Room.StatusChoices.CLOSED, force_close="true")

        assert Debt.objects.get(room=room, force_settled_at__isnull=False).settled
        assert Debt.objects.get(room=room, force_settled_at__isnull=True).settled

    def test_a_failing_debt_update_rolls_the_room_back(self, post_status: Callable, room: Room) -> None:
        user_a, user_b = room.users.all()[:2]
        Debt.objects.create(room=room, debitor=user_a, creditor=user_b, value=5, currency=room.preferred_currency)

        with (
            mock.patch.object(DebtQuerySet, "update", side_effect=DatabaseError),
            pytest.raises(DatabaseError),
        ):
            post_status(room, status=Room.StatusChoices.CLOSED, force_close="true")

        room.refresh_from_db()
        assert room.status == Room.StatusChoices.OPEN
        assert Debt.objects.get(room=room).settled is False
