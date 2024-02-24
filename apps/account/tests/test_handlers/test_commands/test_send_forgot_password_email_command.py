from unittest import mock

from apps.account.handlers.commands.send_forgot_password_email import handle_send_forgot_password_email
from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.messages.events.forgot_password_email_sent import ForgotPasswordEmailSent
from apps.core.tests.setup import BaseTestSetUp
from apps.mail.services.forgot_password_mail_service import ForgotPasswordEmailService


class SendForgotPasswordEmailHandlerTestCase(BaseTestSetUp):
    def test_regular(self):
        context = {"user": self.user}
        with (
            mock.patch.object(ForgotPasswordEmailService, "__init__", return_value=None) as mocked_init,
            mock.patch.object(ForgotPasswordEmailService, "process") as mocked_process,
        ):
            ret = handle_send_forgot_password_email(context=SendForgotPasswordEmail.Context(**context))
            mocked_init.assert_called_once_with(recipient=self.user)
            mocked_process.assert_called_once()

        self.assertIsInstance(ret, ForgotPasswordEmailSent)

        self.assertEqual(ret.Context.__dict__, context)
