from collections.abc import Callable
from unittest import mock

import pytest
from django.core import mail
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.handlers.events.notify_on_room_debts_force_settled import (
    send_email_on_room_debts_force_settled,
    send_notification_on_room_debts_force_settled,
)
from apps.room.messages.events.room_debts_force_settled import RoomDebtsForceSettled
from apps.room.models import Room

pytestmark = pytest.mark.django_db

HANDLERS = "apps.room.handlers.events.notify_on_room_debts_force_settled"


class TestForceCloseNotification:
    def test_the_event_names_debtors_and_creditors(
        self, post_status: Callable, room_with_settled_and_open_debt: Room, user: User, guest_user: User
    ) -> None:
        _, handle_message = post_status(
            room_with_settled_and_open_debt, status=Room.StatusChoices.CLOSED, force_close="true"
        )

        event = handle_message.call_args_list[0].args[0]
        assert isinstance(event, RoomDebtsForceSettled)
        assert set(event.Context.affected_user_ids) == {user.id, guest_user.id}
        assert event.Context.actor == user

    def test_a_normal_close_fires_no_force_event(self, post_status: Callable, room: Room) -> None:
        _, handle_message = post_status(room, status=Room.StatusChoices.CLOSED)

        assert not any(isinstance(call.args[0], RoomDebtsForceSettled) for call in handle_message.call_args_list)

    def test_push_goes_to_affected_members_but_not_the_actor_or_bystanders(self, room: Room, user: User) -> None:
        debtor = UserFactory(language="de")
        room.users.add(debtor, UserFactory())
        context = RoomDebtsForceSettled.Context(room=room, actor=user, affected_user_ids=[user.id, debtor.id])

        with mock.patch(f"{HANDLERS}.Notification") as notification:
            send_notification_on_room_debts_force_settled(context)

        notification.return_value.send_to_user.assert_called_once_with(debtor)
        payload = notification.Payload.call_args.kwargs
        assert payload["head"] == "Schulden als beglichen markiert"
        assert room.name in payload["body"]
        assert payload["click_url"] == reverse("debt:list", kwargs={"room_slug": room.slug})

    def test_mail_skips_guests_and_the_actor(self, room: Room, user: User, guest_user: User) -> None:
        debtor = UserFactory()
        room.users.add(debtor)
        context = RoomDebtsForceSettled.Context(
            room=room, actor=user, affected_user_ids=[user.id, guest_user.id, debtor.id]
        )

        with mock.patch(f"{HANDLERS}.RoomDebtsForceSettledEmailService") as service:
            send_email_on_room_debts_force_settled(context)

        service.assert_called_once_with(recipient=debtor, room=room, actor_name=user.name)
        service.return_value.process.assert_called_once()

    def test_the_mail_renders_in_the_recipients_language(self, room: Room, user: User) -> None:
        debtor = UserFactory(language="de")

        send_email_on_room_debts_force_settled(
            RoomDebtsForceSettled.Context(room=room, actor=user, affected_user_ids=[debtor.id])
        )

        assert len(mail.outbox) == 1
        assert "als beglichen markiert" in mail.outbox[0].subject
        assert mail.outbox[0].to == [debtor.email]
