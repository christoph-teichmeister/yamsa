from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.mail.services.base_email_service import BaseYamsaEmailService, EmailExtraContext, EmailUserTextContext
from apps.room.models import Room


class RoomDebtsForceSettledEmailService(BaseYamsaEmailService):
    def __init__(self, recipient: User, *, room: Room, actor_name: str) -> None:
        self.room = room
        self.actor_name = actor_name
        super().__init__(recipient=recipient)

    def get_subject(self) -> str:
        # Called outside the language override that get_context_data applies, so it sets its own.
        with translation.override(self.get_language_code()):
            return gettext("%(room_name)s | Open debts marked as settled") % {"room_name": self.room.name}

    def get_email_user_text_context(self) -> EmailUserTextContext:
        return EmailUserTextContext(
            text_list=[
                _('%(actor)s closed "%(room_name)s" and marked all its open debts as settled.')
                % {"actor": self.actor_name, "room_name": self.room.name},
                _("Nobody has to pay them. If that is wrong, the room can be reopened and the debts restored."),
            ]
        )

    def get_email_extra_context(self) -> EmailExtraContext:
        return EmailExtraContext(
            show_cta=True,
            cta_link=f"{settings.BACKEND_URL}{reverse('debt:list', kwargs={'room_slug': self.room.slug})}",
            cta_label=_("See the debts"),
        )
