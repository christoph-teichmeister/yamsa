from unittest import mock

import pytest

from apps.account.handlers.commands.send_forgot_password_email import handle_send_forgot_password_email
from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.messages.events.forgot_password_email_sent import ForgotPasswordEmailSent
from apps.mail.services.forgot_password_mail_service import ForgotPasswordEmailService


@pytest.mark.django_db
class TestSendForgotPasswordEmailHandler:
    def test_regular(self, user):
        context = {"user": user}

        with (
            mock.patch.object(ForgotPasswordEmailService, "__init__", return_value=None) as mocked_init,
            mock.patch.object(ForgotPasswordEmailService, "process") as mocked_process,
        ):
            result = handle_send_forgot_password_email(context=SendForgotPasswordEmail.Context(**context))
            mocked_init.assert_called_once_with(recipient=user)
            mocked_process.assert_called_once()

        assert isinstance(result, ForgotPasswordEmailSent)
        assert result.Context.__dict__ == context
