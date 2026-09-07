import pytest

from apps.room.forms.room_edit_form import RoomEditForm
from apps.room.models import Room

pytestmark = pytest.mark.django_db


def test_the_form_persists_the_rooms_own_fields(room: Room, user):
    form = RoomEditForm(
        data={
            "name": "Renamed room",
            "description": "A new description",
            "preferred_currency": room.preferred_currency.pk,
        },
        instance=room,
    )
    form.user = user

    assert form.is_valid(), form.errors
    saved_room = form.save()

    assert saved_room.name == "Renamed room"
    assert saved_room.description == "A new description"
    assert saved_room.lastmodified_by == user


def test_the_status_is_not_one_of_the_fields(room: Room, user):
    """Closing a room runs on its own cycle, so this form must not be able to flip it."""
    form = RoomEditForm(
        data={
            "name": room.name,
            "description": room.description,
            "preferred_currency": room.preferred_currency.pk,
            "status": Room.StatusChoices.CLOSED,
        },
        instance=room,
    )
    form.user = user

    assert form.is_valid(), form.errors
    assert form.save().status == Room.StatusChoices.OPEN
