from unittest import mock

import pytest

from apps.account.tests.factories import UserFactory
from apps.mail.services.user_added_to_room_mail_service import UserAddedToRoomEmailService
from apps.room.handlers.events.notify_on_user_connection_to_room_created import (
    send_email_on_user_connection_to_room_created,
)
from apps.room.messages.events.user_connection_to_room_created import UserConnectionToRoomCreated
from apps.room.tests.factories import UserConnectionToRoomFactory


@pytest.mark.django_db
class TestSendEmailOnUserConnectionToRoomCreated:
    def test_returns_none_for_non_guest_non_creator(self, room, user):
        another_user = UserFactory()
        ucr = UserConnectionToRoomFactory(user=another_user, room=room, created_by=user)

        with (
            mock.patch.object(UserAddedToRoomEmailService, "__init__", return_value=None),
            mock.patch.object(UserAddedToRoomEmailService, "process"),
        ):
            result = send_email_on_user_connection_to_room_created(
                context=UserConnectionToRoomCreated.Context(instance=ucr)
            )

        assert result is None

    def test_returns_none_for_guest(self, room, guest_user, user):
        ucr = UserConnectionToRoomFactory(user=guest_user, room=room, created_by=user)

        result = send_email_on_user_connection_to_room_created(
            context=UserConnectionToRoomCreated.Context(instance=ucr)
        )

        assert result is None
