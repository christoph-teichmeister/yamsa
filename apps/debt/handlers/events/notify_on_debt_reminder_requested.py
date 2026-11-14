from django.conf import settings
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from apps.account.utils.language import get_language_code_for_user
from apps.core.event_loop.registry import message_registry
from apps.debt.messages.events.debt_reminder_requested import DebtReminderRequested
from apps.mail.services.manual_payment_reminder_mail_service import ManualPaymentReminderEmailService
from apps.webpush.utils import Notification


def _amount(context: DebtReminderRequested.Context) -> str:
    return f"{context.debt.value}{context.debt.currency.sign}"


@message_registry.register_event(event=DebtReminderRequested, atomic=False)
def send_notification_on_debt_reminder_requested(context: DebtReminderRequested.Context) -> None:
    debt = context.debt

    with translation.override(get_language_code_for_user(debt.debitor)):
        head = _("Payment reminder")
        body = _('{creditor} gently reminds you of {amount} in "{room}"').format(
            creditor=debt.creditor.name, amount=_amount(context), room=debt.room.name
        )

    Notification(
        payload=Notification.Payload(
            head=head,
            body=body,
            click_url=reverse("debt:list", kwargs={"room_slug": debt.room.slug}),
        ),
    ).send_to_user(debt.debitor)


@message_registry.register_event(event=DebtReminderRequested, atomic=False)
def send_email_on_debt_reminder_requested(context: DebtReminderRequested.Context) -> None:
    debt = context.debt

    # Guests have no real address; the opt-out is the same switch the automatic reminder honours.
    if debt.debitor.is_guest or not debt.debitor.wants_to_receive_payment_reminders:
        return

    backend = settings.BACKEND_URL.rstrip("/")
    ManualPaymentReminderEmailService(
        recipient=debt.debitor,
        creditor_name=debt.creditor.name,
        room_name=debt.room.name,
        amount_summary=_amount(context),
        payment_link=f"{backend}{reverse('debt:list', kwargs={'room_slug': debt.room.slug})}",
    ).process()
