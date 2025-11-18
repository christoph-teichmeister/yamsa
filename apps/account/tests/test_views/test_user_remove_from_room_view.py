import http
import json
from unittest import mock

from django.urls import reverse

from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.models import User
from apps.account.views import UserListForRoomView
from apps.core.tests.setup import BaseTestSetUp
from apps.core.toast_constants import ERROR_TOAST_CLASS
from apps.room.views import RoomListView


class UserRemoveFromRoomViewTestCase(BaseTestSetUp):
    def test_post_user_can_not_be_removed_from_room(self):
        self.room.users.add(self.guest_user)

        with (
            mock.patch("apps.account.views.user_remove_from_room_view.handle_message") as mocked_handle_message,
            mock.patch.object(User, "can_be_removed_from_room", return_value=False),
        ):
            client = self.reauthenticate_user(self.user)
            response = client.post(
                reverse(
                    "account:remove-from-room",
                    kwargs={"room_slug": self.room.slug, "pk": self.guest_user.id},
                ),
                follow=True,
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            mocked_handle_message.assert_not_called()

        self.assertTrue(response.template_name[0], UserListForRoomView.template_name)
        payload = json.loads(response.headers["HX-Trigger-After-Settle"])
        toasts = payload["triggerToast"]
        self.assertIsInstance(toasts, list)
        self.assertEqual(
            toasts[0]["message"],
            f'"{self.guest_user.name}" can not be removed from this room, '
            f"because they still have either transactions or open debts.",
        )
        self.assertEqual(toasts[0]["type"], ERROR_TOAST_CLASS)

    def test_post_user_can_be_removed_from_room(self):
        self.room.users.add(self.guest_user)

        with mock.patch("apps.account.views.user_remove_from_room_view.handle_message") as mocked_handle_message:
            client = self.reauthenticate_user(self.user)
            response = client.post(
                reverse(
                    "account:remove-from-room",
                    kwargs={"room_slug": self.room.slug, "pk": self.guest_user.id},
                ),
                follow=True,
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            mocked_handle_message.assert_called_once()
            self.assertIsInstance(mocked_handle_message.call_args[0][0], RemoveUserFromRoom)

        self.assertTrue(response.template_name[0], UserListForRoomView.template_name)

    def test_post_user_removes_themselves_from_room(self):
        self.room.users.add(self.guest_user)

        with mock.patch("apps.account.views.user_remove_from_room_view.handle_message") as mocked_handle_message:
            client = self.reauthenticate_user(self.user)
            response = client.post(
                reverse(
                    "account:remove-from-room",
                    kwargs={"room_slug": self.room.slug, "pk": self.user.id},
                ),
                follow=True,
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            mocked_handle_message.assert_called_once()
            self.assertIsInstance(mocked_handle_message.call_args[0][0], RemoveUserFromRoom)

        self.assertTrue(response.template_name[0], RoomListView.template_name)
