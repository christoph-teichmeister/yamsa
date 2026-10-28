import re

import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail

from apps.account.models import User
from apps.mail.services.forgot_password_mail_service import ForgotPasswordEmailService


@pytest.mark.django_db
class TestForgotPasswordEmailService:
    def test_link_carries_a_valid_reset_token(self, user: User) -> None:
        cta_link = ForgotPasswordEmailService(recipient=user).get_email_extra_context().cta_link

        token = re.search(r"/reset-password/[^/]+/([^/]+)/$", cta_link).group(1)
        assert default_token_generator.check_token(user, token)

    def test_building_the_mail_does_not_touch_the_password(self, user: User) -> None:
        password_before = user.password

        ForgotPasswordEmailService(recipient=user).process()

        user.refresh_from_db()
        assert user.password == password_before
        assert len(mail.outbox) == 1
        assert "/reset-password/" in mail.outbox[0].body or "/reset-password/" in str(mail.outbox[0].alternatives)
