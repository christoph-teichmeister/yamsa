from django.urls import reverse

from apps.core.event_loop.registry import message_registry
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.webpush.dataclasses import Notification


@message_registry.register_event(event=DebtSettled)
def send_notification_on_debt_settled(context: DebtSettled.Context):
    debt = context.debt

    Notification(
        payload=Notification.Payload(
            head="Debt settled",
            body=f"{debt.debitor} just settled their debt of {debt.value}{debt.currency.sign} to you",
            click_url=reverse(viewname="htmx-debt-list", kwargs={"room_slug": debt.room.slug}),
        ),
    ).send_to_user(debt.creditor)
