from datetime import UTC, datetime
from unittest import mock

import pytest
from freezegun import freeze_time

from apps.account.handlers.commands.send_invitation_email import handle_send_invitation_email
from apps.account.messages.commands.send_invitation_email import SendInvitationEmail
from apps.account.messages.events.invitation_email_sent import InvitationEmailSent
from apps.mail.services.invitation_mail_service import InvitationEmailService


@pytest.mark.django_db
@freeze_time("2020-04-04 04:20:00")
class TestSendInvitationEmailHandler:
    def test_regular(self, guest_user, user):
        context = {
            "invitee": guest_user,
            "invitee_email": "invitee_email@local.local",
            "inviter": user,
        }

        with (
            mock.patch.object(InvitationEmailService, "__init__", return_value=None) as mocked_init,
            mock.patch.object(InvitationEmailService, "process") as mocked_process,
        ):
            result = handle_send_invitation_email(context=SendInvitationEmail.Context(**context))
            mocked_init.assert_called_once_with(
                invited_by=user,
                recipient=guest_user,
                recipient_email_list=[context["invitee_email"]],
            )
            mocked_process.assert_called_once()

        assert isinstance(result, InvitationEmailSent)
        assert result.Context.__dict__ == context
        assert guest_user.invitation_email_sent
        assert guest_user.invitation_email_sent_at == datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC)
