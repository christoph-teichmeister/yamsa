from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.account.utils.notification_preferences import (
    PAYMENT_REMINDER_VARIANT,
    build_payment_reminder_unsubscribe_url,
)
from apps.mail.services.base_email_service import (
    BaseYamsaEmailService,
    EmailBaseTextContext,
    EmailExtraContext,
    EmailUserTextContext,
)


class PaymentReminderEmailService(BaseYamsaEmailService):
    FROM_EMAIL = settings.EMAIL_DEFAULT_FROM_EMAIL

    def __init__(self, recipient, *, room_name: str, amount_summary: str, inactivity_days: int, payment_link: str):
        self.room_name = room_name
        self.amount_summary = amount_summary
        self.inactivity_days = inactivity_days
        self.payment_link = payment_link
        self.subject = (_("%(room_name)s | Payment reminder") % {"room_name": self.room_name}) + " ⚡"
        super().__init__(recipient=recipient)

    def get_email_user_text_context(self):
        return EmailUserTextContext(
            text_list=[
                _("Hey there! It has been %(inactivity_days)d days since any activity in %(room_name)s.")
                % {
                    "inactivity_days": self.inactivity_days,
                    "room_name": self.room_name,
                },
                _("You currently owe %(amount_summary)s.")
                % {
                    "amount_summary": self.amount_summary,
                },
                _("Please follow the link below to review and settle the outstanding balance before it grows stale.")
                + " 🕰️",
            ]
        )

    def get_email_base_text_context(self):
        return EmailBaseTextContext(
            header=_("Payment reminder: %(room_name)s") % {"room_name": self.room_name},
            footer=_("This reminder is generated automatically for overdue balances. We're cheering for you!"),
            sub_footer=_("Need a hand? Reach out to your room admin if the numbers look off."),
        )

    def get_email_extra_context(self):
        return EmailExtraContext(
            show_unsubscribe=True,
            unsubscribe_link=build_payment_reminder_unsubscribe_url(
                self.recipient,
                variant=PAYMENT_REMINDER_VARIANT,
            ),
            show_cta=True,
            cta_link=self.payment_link,
            cta_label=_("Review pending debts"),
        )
