from decimal import Decimal
from unittest import mock

from django.utils import timezone

from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt
from apps.room.forms.room_edit_form import RoomEditForm
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room


def _create_open_debt(room: Room) -> Debt:
    if room.users.count() < 2:
        while room.users.count() < 2:
            room.users.add(UserFactory())

    users = list(room.users.all()[:2])
    return Debt.objects.create(
        room=room,
        debitor=users[0],
        creditor=users[1],
        value=Decimal("10.00"),
        currency=room.preferred_currency,
    )


def test_clean_blocks_closing_room_with_open_debts(room: Room):
    _create_open_debt(room)

    form = RoomEditForm(
        data={
            "name": room.name,
            "description": room.description[:50],
            "preferred_currency": room.preferred_currency.pk,
            "status": Room.StatusChoices.CLOSED,
        },
        instance=room,
    )

    assert not form.is_valid()
    assert "status" in form.errors
    assert "open debts" in str(form.errors["status"][0])


def test_force_close_marks_debts_as_settled_and_emits_event(room: Room, user):
    _create_open_debt(room)

    form = RoomEditForm(
        data={
            "name": room.name,
            "description": room.description[:50],
            "preferred_currency": room.preferred_currency.pk,
            "status": Room.StatusChoices.CLOSED,
            "force_close": "on",
        },
        instance=room,
    )
    form.user = user

    with mock.patch("apps.room.forms.room_edit_form.handle_message") as mock_handle_message:
        assert form.is_valid()
        saved_room = form.save()

    debt = Debt.objects.get(room=room)
    assert debt.settled
    assert debt.settled_at == timezone.localdate()
    assert saved_room.status == Room.StatusChoices.CLOSED

    mock_handle_message.assert_called_once()
    message_arg = mock_handle_message.call_args[0][0]
    assert isinstance(message_arg, RoomStatusChanged)
    assert message_arg.Context.room.pk == room.pk
