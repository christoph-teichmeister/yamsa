from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.account.utils.notification_preferences import (
    ROOM_REMINDER_VARIANT,
    build_payment_reminder_unsubscribe_url,
)
from apps.mail.services.base_email_service import (
    BaseYamsaEmailService,
    EmailBaseTextContext,
    EmailExtraContext,
    EmailUserTextContext,
)


class RoomClosureReminderEmailService(BaseYamsaEmailService):
    FROM_EMAIL = settings.EMAIL_DEFAULT_FROM_EMAIL
    subject = _("Room status reminder") + " 🌿"

    def __init__(self, recipient, *, room_name: str, inactivity_days: int, room_link: str):
        self.room_name = room_name
        self.inactivity_days = inactivity_days
        self.room_link = room_link
        self.subject = (
            _("%(room_name)s | Room still open?") % {"room_name": self.room_name}
        ) + " 🌱"
        super().__init__(recipient=recipient)

    def get_email_user_text_context(self):
        return EmailUserTextContext(
            text_list=[
                _("%(room_name)s has been quiet for %(inactivity_days)d days.")
                % {
                    "room_name": self.room_name,
                    "inactivity_days": self.inactivity_days,
                }
                + " 🌙",
                _(
                    "If everyone already settled up, please mark the debts as paid and close the room so it stops lingering."
                )
                + " ✨",
                _(
                    "If you still need the room, feel free to ignore this reminder and keep it open."
                ),
            ]
        )

    def get_email_base_text_context(self):
        return EmailBaseTextContext(
            header=_("Room cleanup reminder: %(room_name)s") % {"room_name": self.room_name},
            footer=_("This reminder is generated automatically when open rooms stay inactive. We're happy to help."),
            sub_footer=_("Give us a shout if the room history looks off."),
        )

    def get_email_extra_context(self):
        return EmailExtraContext(
            show_unsubscribe=True,
            unsubscribe_link=build_payment_reminder_unsubscribe_url(
                self.recipient,
                variant=ROOM_REMINDER_VARIANT,
            ),
            show_cta=True,
            cta_link=self.room_link,
            cta_label=_("Review room status"),
        )
