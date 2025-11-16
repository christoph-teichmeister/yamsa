from django.conf import settings

from apps.account.utils.notification_preferences import build_payment_reminder_unsubscribe_url
from apps.mail.services.base_email_service import (
    BaseYamsaEmailService,
    EmailBaseTextContext,
    EmailExtraContext,
    EmailUserTextContext,
)


class PaymentReminderEmailService(BaseYamsaEmailService):
    FROM_EMAIL = settings.PAYMENT_REMINDER_SENDER_EMAIL
    subject = "Payment reminder ⚠️"

    def __init__(self, recipient, *, room_name: str, amount_summary: str, inactivity_days: int, payment_link: str):
        self.room_name = room_name
        self.amount_summary = amount_summary
        self.inactivity_days = inactivity_days
        self.payment_link = payment_link
        self.subject = f"{self.room_name} | Payment reminder"
        super().__init__(recipient=recipient)

    def get_email_user_text_context(self):
        return EmailUserTextContext(
            text_list=[
                f"It has been {self.inactivity_days} days since any activity in {self.room_name}.",
                f"You currently owe {self.amount_summary}.",
                "Please follow the link below to review and settle the outstanding balance before it grows stale.",
            ]
        )

    def get_email_base_text_context(self):
        return EmailBaseTextContext(
            header=f"Payment reminder · {self.room_name}",
            footer="This reminder is generated automatically for overdue balances.",
            sub_footer="Need a hand? Reach out to your room admin if the numbers look off.",
        )

    def get_email_extra_context(self):
        return EmailExtraContext(
            show_unsubscribe=True,
            unsubscribe_link=build_payment_reminder_unsubscribe_url(self.recipient),
            show_cta=True,
            cta_link=self.payment_link,
            cta_label="Review pending debts",
        )
