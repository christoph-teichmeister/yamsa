from unittest import mock

from apps.account.handlers.commands.send_post_register_email import handle_send_post_register_mail
from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.account.messages.events.post_register_email_sent import PostRegisterEmailSent
from apps.core.tests.setup import BaseTestSetUp
from apps.mail.services.post_register_mail_service import PostRegisterEmailService


class SendPostRegisterEmailHandlerTestCase(BaseTestSetUp):
    def test_regular(self):
        context = {"user": self.user}
        with (
            mock.patch.object(PostRegisterEmailService, "__init__", return_value=None) as mocked_init,
            mock.patch.object(PostRegisterEmailService, "process") as mocked_process,
        ):
            ret = handle_send_post_register_mail(context=SendPostRegisterEmail.Context(**context))
            mocked_init.assert_called_once_with(recipient=self.user)
            mocked_process.assert_called_once()

        self.assertIsInstance(ret, PostRegisterEmailSent)

        self.assertEqual(ret.Context.__dict__, context)
