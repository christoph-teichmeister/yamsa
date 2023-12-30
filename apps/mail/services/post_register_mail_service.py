from typing import Union

from django.conf import settings
from django.urls import reverse

from apps.account.models import User
from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext


class PostRegisterEmailService(BaseYamsaEmailService):
    """Email to invite guests to yamsa"""

    subject = "Welcome to yamsa ❤️"
    user_has_rooms = False

    def __init__(self, recipient: User, recipient_email_list: Union[list, tuple, str] = None, *args, **kwargs) -> None:
        self.user_has_rooms = recipient.room_qs_for_list.exists()
        super().__init__(recipient, recipient_email_list, *args, **kwargs)

    def get_email_user_text_context(self):
        text_list = ["Welcome to yamsa 🥳"]

        if self.user_has_rooms:
            text_list.append("It looks like you already belong to some rooms!")
            text_list.append("Check them out, by clicking the button below ⬇️")
        else:
            text_list.append("Create a new room, by clicking the button below ⬇️")

        return EmailUserTextContext(text_list=text_list)

    def get_email_extra_context(self):
        cta_btn_link = reverse(viewname="room-create")
        cta_btn_text = "Create a room"

        if self.user_has_rooms:
            cta_btn_link = reverse(viewname="room-list")
            cta_btn_text = "See your rooms"

        return EmailExtraContext(
            show_cta=True,
            cta_btn_link=f"{settings.PROJECT_BASE_URL}{cta_btn_link}",
            cta_btn_text=cta_btn_text,
        )
