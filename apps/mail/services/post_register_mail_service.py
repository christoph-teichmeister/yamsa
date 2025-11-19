from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class PostRegisterEmailService(BaseYamsaEmailService):
    subject = _("Welcome to yamsa") + " ❤️"
    user_has_rooms = False

    def __init__(
        self, recipient: User, recipient_email_list: list | (tuple | str) | None = None, *args, **kwargs
    ) -> None:
        self.user_has_rooms = recipient.room_qs_for_list.exists()
        super().__init__(recipient, recipient_email_list, *args, **kwargs)

    def get_email_user_text_context(self):
        text_list = [_("Welcome to yamsa") + " 🥳"]

        if self.user_has_rooms:
            text_list.append(_("It looks like you already belong to some rooms!"))
            text_list.append(_("Check them out, by clicking the button below") + " ⬇️")
        else:
            text_list.append(_("Create a new room, by clicking the button below") + " ⬇️")

        return EmailUserTextContext(text_list=text_list)

    def get_email_extra_context(self):
        cta_btn_link = reverse(viewname="room:create")
        cta_btn_text = _("Create a room")

        if self.user_has_rooms:
            cta_btn_link = reverse(viewname="room:list")
            cta_btn_text = _("See your rooms")

        return EmailExtraContext(
            show_cta=True,
            cta_link=f"{settings.BACKEND_URL}{cta_btn_link}",
            cta_label=cta_btn_text,
        )
