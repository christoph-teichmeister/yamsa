from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext_lazy as _

from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class ForgotPasswordEmailService(BaseYamsaEmailService):
    subject = _("Reset your password") + " 🔑"

    def get_email_user_text_context(self) -> EmailUserTextContext:
        return EmailUserTextContext(
            text_list=[
                _("Forgotten your password?"),
                _("No worries - happens to the best!"),
                "",
                _("Click the button below to choose a new password") + " ⬇️",
                _("If you did not ask for this, you can ignore this email - your password stays as it is."),
            ]
        )

    def get_email_extra_context(self) -> EmailExtraContext:
        reset_path = reverse(
            viewname="account:reset-password",
            kwargs={
                "uidb64": urlsafe_base64_encode(force_bytes(self.recipient.pk)),
                "token": default_token_generator.make_token(self.recipient),
            },
        )
        return EmailExtraContext(
            show_cta=True,
            cta_link=f"{settings.BACKEND_URL}{reset_path}",
            cta_label=_("Choose a new password"),
        )
