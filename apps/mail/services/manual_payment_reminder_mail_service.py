from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.mail.services.base_email_service import EmailBaseTextContext, EmailUserTextContext
from apps.mail.services.payment_reminder_mail_service import PaymentReminderEmailService


class ManualPaymentReminderEmailService(PaymentReminderEmailService):
    """A creditor's own nudge, as opposed to the automatic reminder for quiet rooms."""

    def __init__(
        self, recipient: User, *, creditor_name: str, room_name: str, amount_summary: str, payment_link: str
    ) -> None:
        super().__init__(
            recipient,
            room_name=room_name,
            amount_summary=amount_summary,
            inactivity_days=0,
            payment_link=payment_link,
        )
        self.creditor_name = creditor_name
        self.subject = _("%(creditor_name)s sent you a payment reminder | %(room_name)s") % {
            "creditor_name": creditor_name,
            "room_name": room_name,
        }

    def get_email_user_text_context(self) -> EmailUserTextContext:
        return EmailUserTextContext(
            text_list=[
                _("Hey there! %(creditor_name)s gently reminds you of %(amount_summary)s in %(room_name)s.")
                % {
                    "creditor_name": self.creditor_name,
                    "amount_summary": self.amount_summary,
                    "room_name": self.room_name,
                },
                _("No rush - follow the link below whenever it suits you to review the debt and mark it as paid."),
            ]
        )

    def get_email_base_text_context(self) -> EmailBaseTextContext:
        return EmailBaseTextContext(
            header=_("Payment reminder: %(room_name)s") % {"room_name": self.room_name},
            footer=_("%(creditor_name)s sent this reminder from yamsa.") % {"creditor_name": self.creditor_name},
            sub_footer=_("Already paid? Just mark the debt as paid and this reminder is out of the way."),
        )
