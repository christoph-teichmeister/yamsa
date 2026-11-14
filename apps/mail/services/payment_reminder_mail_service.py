from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
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

    def __init__(
        self,
        recipient: User,
        *,
        room_name: str,
        amount_summary: str,
        creditor_names: tuple[str, ...],
        inactivity_days: int,
        payment_link: str,
    ) -> None:
        self.room_name = room_name
        self.amount_summary = amount_summary
        self.creditor_names = creditor_names
        self.inactivity_days = inactivity_days
        self.payment_link = payment_link
        self.subject = (_("%(room_name)s | Payment reminder") % {"room_name": self.room_name}) + " ⚡"
        super().__init__(recipient=recipient)

    def get_email_user_text_context(self) -> EmailUserTextContext:
        return EmailUserTextContext(
            text_list=[
                _("It has been %(inactivity_days)d days since any activity in %(room_name)s.")
                % {
                    "inactivity_days": self.inactivity_days,
                    "room_name": self.room_name,
                },
                _("You still owe %(amount_summary)s to %(creditors)s.")
                % {
                    "amount_summary": self.amount_summary,
                    "creditors": ", ".join(self.creditor_names),
                },
                _("Whenever you have a moment, the link below shows what is open and lets you settle it."),
            ]
        )

    def get_email_base_text_context(self) -> EmailBaseTextContext:
        return EmailBaseTextContext(
            header=_("Payment reminder: %(room_name)s") % {"room_name": self.room_name},
            footer=_("This reminder is sent automatically when a room has been quiet and a balance is still open."),
            sub_footer=_("Something looks off? Reply to this email and we will take a look."),
        )

    def get_email_extra_context(self) -> EmailExtraContext:
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
