from django.conf import settings

from apps.account.utils.notification_preferences import build_payment_reminder_unsubscribe_url
from apps.mail.services.base_email_service import (
    BaseYamsaEmailService,
    EmailBaseTextContext,
    EmailExtraContext,
    EmailUserTextContext,
)


class RoomClosureReminderEmailService(BaseYamsaEmailService):
    FROM_EMAIL = settings.PAYMENT_REMINDER_SENDER_EMAIL
    subject = "Room status reminder"

    def __init__(self, recipient, *, room_name: str, inactivity_days: int, room_link: str):
        self.room_name = room_name
        self.inactivity_days = inactivity_days
        self.room_link = room_link
        self.subject = f"{self.room_name} | Room still open?"
        super().__init__(recipient=recipient)

    def get_email_user_text_context(self):
        return EmailUserTextContext(
            text_list=[
                f"{self.room_name} has been quiet for {self.inactivity_days} days.",
                "If everyone already settled up, please mark the debts as paid and close the room so it stops lingering.",
                "If you still need the room, feel free to ignore this reminder and keep it open.",
            ]
        )

    def get_email_base_text_context(self):
        return EmailBaseTextContext(
            header=f"Room cleanup reminder · {self.room_name}",
            footer="This reminder is generated automatically when open rooms stay inactive.",
            sub_footer="Give us a shout if the room history looks off.",
        )

    def get_email_extra_context(self):
        return EmailExtraContext(
            show_unsubscribe=True,
            unsubscribe_link=build_payment_reminder_unsubscribe_url(self.recipient),
            show_cta=True,
            cta_link=self.room_link,
            cta_label="Review room status",
        )
