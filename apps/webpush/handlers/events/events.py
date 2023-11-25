from django.urls import reverse

from apps.core.event_loop.registry import message_registry
from apps.transaction.messages.events.transaction import ParentTransactionCreated, ParentTransactionUpdated
from apps.transaction.models import ChildTransaction
from apps.webpush.dataclasses import Notification


@message_registry.register_event(event=ParentTransactionCreated)
def send_notification_on_transaction_create(context: ParentTransactionCreated.Context):
    parent_transaction = context.parent_transaction

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        # If a user created this transaction on another ones behalf and is a debtor, do not notify them
        if parent_transaction.created_by == child_transaction.paid_for:
            continue

        Notification(
            payload=Notification.Payload(
                head="Transaction created",
                body=f"{parent_transaction.paid_by.name} just paid "
                f"{parent_transaction.value}{parent_transaction.currency.sign} "
                f'("{parent_transaction.description}")\n'
                f"Have a look!",
                click_url=reverse(
                    viewname="htmx-transaction-detail",
                    kwargs={
                        "room_slug": parent_transaction.room.slug,
                        "pk": parent_transaction.id,
                    },
                ),
            ),
        ).send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=ParentTransactionUpdated)
def send_notification_on_transaction_update(context: ParentTransactionUpdated.Context):
    parent_transaction = context.parent_transaction

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        Notification(
            payload=Notification.Payload(
                head="Transaction updated",
                body=f"{parent_transaction.lastmodified_by.name} just updated a transaction "
                f'("{parent_transaction.description}")\n'
                f"Have a look!",
                click_url=reverse(
                    viewname="htmx-transaction-detail",
                    kwargs={
                        "room_slug": parent_transaction.room.slug,
                        "pk": parent_transaction.id,
                    },
                ),
            ),
        ).send_to_user(child_transaction.paid_for)
