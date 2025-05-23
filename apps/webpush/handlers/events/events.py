from django.urls import reverse

from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.core.event_loop.registry import message_registry
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.transaction.messages.events.transaction import (
    ChildTransactionDeleted,
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionUpdated,
)
from apps.transaction.models import ChildTransaction
from apps.webpush.utils import Notification


@message_registry.register_event(event=ParentTransactionCreated)
def send_notification_on_transaction_create(context: ParentTransactionCreated.Context):
    parent_transaction = context.parent_transaction

    notification = Notification(
        payload=Notification.Payload(
            head="Transaction created",
            body=f"{parent_transaction.paid_by.name} just paid "
            f"{parent_transaction.value}{parent_transaction.currency.sign} "
            f'("{parent_transaction.description}")\n'
            f"Have a look!",
            click_url=reverse(
                viewname="transaction:detail",
                kwargs={"room_slug": parent_transaction.room.slug, "pk": parent_transaction.id},
            ),
        ),
    )

    # If a user, who is not the creditor, created this transaction, notify the creditor
    if parent_transaction.created_by != parent_transaction.paid_by:
        notification.send_to_user(parent_transaction.paid_by)

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        # If a user created this transaction on another ones behalf and is a debtor, do not notify them
        if (
            parent_transaction.created_by == child_transaction.paid_for
            or parent_transaction.paid_by == child_transaction.paid_for
        ):
            continue

        notification.send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=ChildTransactionDeleted)
@message_registry.register_event(event=ParentTransactionUpdated)
def send_notification_on_transaction_update(context: ParentTransactionUpdated.Context):
    parent_transaction = context.parent_transaction

    notification = Notification(
        payload=Notification.Payload(
            head="Transaction updated",
            body=f"{parent_transaction.lastmodified_by.name} just updated a transaction "
            f'("{parent_transaction.description}")\n'
            f"Have a look!",
            click_url=reverse(
                viewname="transaction:detail",
                kwargs={"room_slug": parent_transaction.room.slug, "pk": parent_transaction.id},
            ),
        ),
    )

    # If a user, who is not the creditor, updated this transaction, notify the creditor
    if parent_transaction.lastmodified_by != parent_transaction.paid_by:
        notification.send_to_user(parent_transaction.paid_by)

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        # If a user updated this transaction on another ones behalf and is a debtor, do not notify them
        if parent_transaction.lastmodified_by == child_transaction.paid_for:
            continue

        notification.send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=ParentTransactionDeleted)
def send_notification_on_child_transaction_deleted(context: ParentTransactionDeleted.Context):
    parent_transaction = context.parent_transaction

    notification = Notification(
        payload=Notification.Payload(
            head="Transaction deleted",
            body=f"{context.user_who_deleted.name} just deleted a transaction "
            f'("{parent_transaction.description}")\n'
            f"Have a look!",
            click_url=reverse(
                viewname="transaction:list",
                kwargs={
                    "room_slug": parent_transaction.room.slug,
                },
            ),
        ),
    )

    notification.send_to_user(parent_transaction.paid_by)

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        # If a user updated this transaction on another ones behalf and is a debtor, do not notify them
        if parent_transaction.lastmodified_by == child_transaction.paid_for:
            continue

        notification.send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=DebtSettled)
def send_notification_on_debt_settled(context: DebtSettled.Context):
    debt = context.debt

    Notification(
        payload=Notification.Payload(
            head="Debt settled",
            body=f"{debt.debitor} just settled their debt of {debt.value}{debt.currency.sign} to you",
            click_url=reverse(viewname="debt:list", kwargs={"room_slug": debt.room.slug}),
        ),
    ).send_to_user(debt.creditor)


@message_registry.register_event(event=UserRemovedFromRoom)
def send_notification_on_user_removed_from_room(context: UserRemovedFromRoom.Context):
    notification = Notification(
        payload=Notification.Payload(
            head="User removed",
            body=f"{context.user_requesting_removal.name} just removed "
            f"{context.user_to_be_removed.name} from {context.room.name}",
            click_url=reverse(viewname="account:list", kwargs={"room_slug": context.room.slug}),
        ),
    )

    for user in context.room.users.exclude(id=context.user_requesting_removal.id):
        notification.send_to_user(user)
