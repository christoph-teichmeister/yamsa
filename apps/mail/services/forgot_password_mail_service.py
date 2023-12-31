from django.conf import settings
from django.urls import reverse

from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class ForgotPasswordEmailService(BaseYamsaEmailService):
    subject = "New Password 🔑"

    email_extra_context = EmailExtraContext(
        show_cta=True,
        cta_btn_link=f"{settings.PROJECT_BASE_URL}{reverse(viewname='account-user-login')}",
        cta_btn_text="Log in with new password",
    )

    def get_email_user_text_context(self):
        new_password = self.recipient.generate_random_password_with_length(10)

        text_list = [
            "Forgotten your password?",
            "No worries - happens to the best!",
            "",
            "Your new password is:",
            f"{new_password}",
            "",
            "Log in with your new password, by clicking the button below ⬇️",
            "(And don't forget to change your password afterwards!)",
        ]

        return EmailUserTextContext(text_list=text_list)
