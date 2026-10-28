from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.account.utils.guest_registration_token import build_guest_registration_token
from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class InvitationEmailService(BaseYamsaEmailService):
    """Email to invite guests to yamsa."""

    subject = _("Invitation") + " 🥳"

    def __init__(self, invited_by: User, *args: object, **kwargs: object) -> None:
        self.invited_by = invited_by
        super().__init__(*args, **kwargs)

    def get_email_user_text_context(self) -> EmailUserTextContext:
        return EmailUserTextContext(
            text_list=[
                _("You have been invited by %(inviter)s to join your friends on yamsa")
                % {
                    "inviter": self.invited_by.name,
                }
                + " 🥳",
                _("Click the button below to register!"),
            ]
        )

    def get_email_extra_context(self) -> EmailExtraContext:
        query = urlencode(
            {
                "with_email": self.recipient_email_list[0],
                "guest_token": build_guest_registration_token(self.recipient.id),
            }
        )
        return EmailExtraContext(
            show_cta=True,
            cta_link=f"{settings.BACKEND_URL}{reverse(viewname='account:register')}?{query}",
            cta_label=_("Register here"),
        )
