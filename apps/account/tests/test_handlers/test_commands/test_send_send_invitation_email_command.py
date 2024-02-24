from datetime import UTC, datetime
from unittest import mock

from freezegun import freeze_time

from apps.account.handlers.commands.send_invitation_email import handle_send_invitation_email
from apps.account.messages.commands.send_invitation_email import SendInvitationEmail
from apps.account.messages.events.invitation_email_sent import InvitationEmailSent
from apps.core.tests.setup import BaseTestSetUp
from apps.mail.services.invitation_mail_service import InvitationEmailService


@freeze_time("2020-04-04 04:20:00")
class SendInvitationEmailHandlerTestCase(BaseTestSetUp):
    def test_regular(self):
        context = {"invitee": self.guest_user, "invitee_email": "invitee_email@local.local", "inviter": self.user}
        with (
            mock.patch.object(InvitationEmailService, "__init__", return_value=None) as mocked_init,
            mock.patch.object(InvitationEmailService, "process") as mocked_process,
        ):
            ret = handle_send_invitation_email(context=SendInvitationEmail.Context(**context))
            mocked_init.assert_called_once_with(
                invited_by=context["inviter"],
                recipient=context["invitee"],
                recipient_email_list=[context["invitee_email"]],
            )
            mocked_process.assert_called_once()

        self.assertIsInstance(ret, InvitationEmailSent)

        self.assertEqual(ret.Context.__dict__, context)

        self.assertTrue(self.guest_user.invitation_email_sent)
        self.assertEqual(self.guest_user.invitation_email_sent_at, datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC))
