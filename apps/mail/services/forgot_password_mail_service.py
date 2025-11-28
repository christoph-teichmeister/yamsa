from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class ForgotPasswordEmailService(BaseYamsaEmailService):
    subject = _("New Password") + " 🔑"

    email_extra_context = EmailExtraContext(
        show_cta=True,
        cta_link=f"{settings.BACKEND_URL}{reverse(viewname='account:login')}",
        cta_label=_("Log in with new password"),
    )

    def get_email_user_text_context(self):
        new_password = self.recipient.generate_random_password_with_length(10)

        text_list = [
            _("Forgotten your password?"),
            _("No worries - happens to the best!"),
            "",
            _("Your new password is:"),
            f"{new_password}",
            "",
            _("Log in with your new password, by clicking the button below") + " ⬇️",
            _("(And don't forget to change your password afterwards!)"),
        ]

        return EmailUserTextContext(text_list=text_list)
