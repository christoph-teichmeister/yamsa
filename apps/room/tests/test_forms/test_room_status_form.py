from decimal import Decimal

import pytest

from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.room.forms.room_status_form import RoomStatusForm
from apps.room.models import Room

pytestmark = pytest.mark.django_db


def create_open_debt(room: Room) -> Debt:
    missing_users = 2 - room.users.count()
    if missing_users > 0:
        room.users.add(*[UserFactory() for _ in range(missing_users)])

    users = list(room.users.all()[:2])
    if len(users) < 2:
        msg = "Room requires at least two users to create an open debt"
        raise AssertionError(msg)
    return Debt.objects.create(
        room=room,
        debitor=users[0],
        creditor=users[1],
        value=Decimal("10.00"),
        currency=room.preferred_currency,
    )


def test_clean_blocks_closing_a_room_with_open_debts(room: Room):
    create_open_debt(room)

    form = RoomStatusForm(data={"status": Room.StatusChoices.CLOSED}, instance=room)

    assert not form.is_valid()
    assert "status" in form.errors
    assert "open debts" in str(form.errors["status"][0])


def test_the_force_flag_lets_a_room_with_open_debts_close(room: Room, user):
    create_open_debt(room)

    form = RoomStatusForm(data={"status": Room.StatusChoices.CLOSED, "force_close": "true"}, instance=room)
    form.user = user

    assert form.is_valid()
    assert form.closes_the_room
    saved_room = form.save()

    assert saved_room.status == Room.StatusChoices.CLOSED
    # Settling the debts is the view's job, so the form must not have touched them.
    assert not Debt.objects.get(room=room).settled


def test_a_settled_room_closes_without_the_force_flag(room: Room, user):
    form = RoomStatusForm(data={"status": Room.StatusChoices.CLOSED}, instance=room)
    form.user = user

    assert form.is_valid()
    assert form.closes_the_room
    assert form.save().status == Room.StatusChoices.CLOSED


def test_reopening_is_not_a_closing_transition(room: Room, user):
    room.status = Room.StatusChoices.CLOSED
    room.save()

    form = RoomStatusForm(data={"status": Room.StatusChoices.OPEN}, instance=room)
    form.user = user

    assert form.is_valid()
    assert not form.closes_the_room
    assert form.save().status == Room.StatusChoices.OPEN


def test_saving_a_closed_room_again_is_not_a_transition(room: Room, user):
    """A post that repeats the stored status must not count as closing it."""
    room.status = Room.StatusChoices.CLOSED
    room.save()
    create_open_debt(room)

    form = RoomStatusForm(data={"status": Room.StatusChoices.CLOSED}, instance=room)
    form.user = user

    assert form.is_valid()
    assert not form.closes_the_room
