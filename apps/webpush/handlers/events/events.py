from typing import Union

from django.urls import reverse

from apps.core.event_loop.registry import message_registry
from apps.transaction.messages.events.transaction import ParentTransactionCreated, ParentTransactionUpdated
from apps.transaction.models import ChildTransaction
from apps.webpush.dataclasses import Notification


@message_registry.register_event(event=ParentTransactionCreated)
@message_registry.register_event(event=ParentTransactionUpdated)
def send_notification_on_transaction_create_or_update(
    context: Union[ParentTransactionCreated.Context | ParentTransactionUpdated.Context],
):
    action_string = "created" if isinstance(context, ParentTransactionCreated.Context) else "updated"
    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=context.parent_transaction.id):
        Notification(
            payload=Notification.Payload(
                head=f"Transaction {action_string}",
                body=f"{context.parent_transaction.lastmodified_by.name} just {action_string} a transaction. "
                f"Have a look!",
                click_url=reverse(viewname="room-detail", kwargs={"slug": context.parent_transaction.room.slug}),
            ),
        ).send_to_user(child_transaction.paid_for)
