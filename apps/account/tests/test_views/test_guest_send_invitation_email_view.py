import http
from unittest import mock

from django.urls import reverse

from apps.account.messages.commands.send_invitation_email import SendInvitationEmail
from apps.account.views import GuestSendInvitationEmailView, UserListForRoomView
from apps.core.tests.setup import BaseTestSetUp


class GuestSendInvitationEmailViewTestCase(BaseTestSetUp):
    def test_get_regular(self):
        client = self.reauthenticate_user(self.user)
        response = client.get(
            reverse(
                "account:guest-send-invitation-email", kwargs={"room_slug": self.room.slug, "pk": self.guest_user.id}
            )
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], GuestSendInvitationEmailView.template_name)
        self.assertIn(f'Invite {self.guest_user.name} to "{self.room.name}"', str(response.content))

        self.assertEqual(response.context_data["active_tab"], "people")

    def test_post_regular(self):
        client = self.reauthenticate_user(self.user)

        with mock.patch("apps.account.views.guest_send_invitation_email_view.handle_message") as mocked_handle_message:
            response = client.post(
                reverse(
                    "account:guest-send-invitation-email",
                    kwargs={"room_slug": self.room.slug, "pk": self.guest_user.id},
                ),
                data={"email": "some_email@local.local"},
                follow=True,
            )
            self.assertEqual(response.status_code, http.HTTPStatus.OK)

            mocked_handle_message.assert_called_once()
            self.assertIsInstance(mocked_handle_message.call_args[0][0], SendInvitationEmail)

        self.assertTrue(response.template_name[0], UserListForRoomView.template_name)
        response_content = response.content.decode()
        self.assertIn("Room roster", response_content)
        self.assertIn("Add guest", response_content)

        self.assertEqual(response.context_data["active_tab"], "people")

    def test_post_email_invalid(self):
        client = self.reauthenticate_user(self.user)

        response = client.post(
            reverse(
                "account:guest-send-invitation-email",
                kwargs={"room_slug": self.room.slug, "pk": self.guest_user.id},
            ),
            data={"email": "invalid_email_format"},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], GuestSendInvitationEmailView.template_name)
        self.assertIn("Enter a valid email address.", str(response.content))

        self.assertEqual(response.context_data["active_tab"], "people")
