from unittest import mock

import pytest

from apps.account.handlers.commands.send_post_register_email import handle_send_post_register_mail
from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.account.messages.events.post_register_email_sent import PostRegisterEmailSent
from apps.mail.services.post_register_mail_service import PostRegisterEmailService


@pytest.mark.django_db
class TestSendPostRegisterEmailHandler:
    def test_regular(self, user):
        context = {"user": user}

        with (
            mock.patch.object(PostRegisterEmailService, "__init__", return_value=None) as mocked_init,
            mock.patch.object(PostRegisterEmailService, "process") as mocked_process,
        ):
            result = handle_send_post_register_mail(context=SendPostRegisterEmail.Context(**context))
            mocked_init.assert_called_once_with(recipient=user)
            mocked_process.assert_called_once()

        assert isinstance(result, PostRegisterEmailSent)
        assert result.Context.__dict__ == context
