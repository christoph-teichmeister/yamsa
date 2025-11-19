from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext
from apps.room.models import Room


class UserAddedToRoomEmailService(BaseYamsaEmailService):
    new_room: Room = None

    def __init__(self, new_room: Room, *args, **kwargs) -> None:
        self.new_room = new_room
        super().__init__(*args, **kwargs)

    def get_subject(self) -> str:
        return (_("Welcome to %(room_name)s") % {"room_name": self.new_room.name}) + " 🥳"

    def get_email_user_text_context(self):
        return EmailUserTextContext(
            text_list=[
                _("You have been invited to %(room_name)s to join your friends")
                % {"room_name": self.new_room.name}
                + " 🥳",
                _("Click the button below to view the room!"),
            ]
        )

    def get_email_extra_context(self):
        cta_btn_link = f"{settings.BACKEND_URL}{reverse('room:detail', kwargs={'room_slug': self.new_room.slug})}"
        return EmailExtraContext(
            show_cta=True,
            cta_link=cta_btn_link,
            cta_label=_("See the room"),
        )
