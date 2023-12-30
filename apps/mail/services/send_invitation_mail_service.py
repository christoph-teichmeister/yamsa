from django.conf import settings

from apps.account.models import User
from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class InvitationEmailService(BaseYamsaEmailService):
    """Email to invite guests to yamsa"""

    subject = "Invitation 🥳"

    def __init__(self, invited_by: User, *args, **kwargs) -> None:
        self.invited_by = invited_by
        super().__init__(*args, **kwargs)

    def get_email_user_text_context(self):
        return EmailUserTextContext(
            text_list=[
                f"You have been invited by {self.invited_by.name} to join your friends on yamsa 🥳",
                "Click the button below to register!",
            ]
        )

    def get_email_extra_context(self):
        return EmailExtraContext(
            show_cta=True,
            cta_btn_link=f"{settings.PROJECT_BASE_URL}/account/register/?with_email={self.recipient_email_list[0]}&for_guest={self.email_user_text_context.user.id}",
            cta_btn_text="Register here",
        )
