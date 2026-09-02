from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.account.models import User
from apps.account.utils.language import get_language_code_for_user
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

    def build_notification_for_user(user: User) -> Notification:
        language_code = get_language_code_for_user(user)
        with translation.override(language_code):
            if not parent_transaction.created_by or parent_transaction.created_by == parent_transaction.paid_by:
                body = _('{payer} logged a payment of {amount}{currency} ("{description}")\nHave a look!').format(
                    payer=parent_transaction.paid_by.name,
                    amount=parent_transaction.value,
                    currency=parent_transaction.currency.sign,
                    description=parent_transaction.description,
                )
            else:
                body = _(
                    '{creator} logged that {payer} paid {amount}{currency} ("{description}")\nHave a look!',
                ).format(
                    creator=parent_transaction.created_by.name,
                    payer=parent_transaction.paid_by.name,
                    amount=parent_transaction.value,
                    currency=parent_transaction.currency.sign,
                    description=parent_transaction.description,
                )

            head = _("Transaction created")

        return Notification(
            payload=Notification.Payload(
                head=head,
                body=body,
                click_url=reverse(
                    viewname="transaction:detail",
                    kwargs={"room_slug": parent_transaction.room.slug, "pk": parent_transaction.id},
                ),
            ),
        )

    # If a user, who is not the creditor, created this transaction, notify the creditor
    if parent_transaction.created_by != parent_transaction.paid_by:
        build_notification_for_user(parent_transaction.paid_by).send_to_user(parent_transaction.paid_by)

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        # If a user created this transaction on another ones behalf and is a debtor, do not notify them
        if (
            parent_transaction.created_by == child_transaction.paid_for
            or parent_transaction.paid_by == child_transaction.paid_for
        ):
            continue

        build_notification_for_user(child_transaction.paid_for).send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=ChildTransactionDeleted)
@message_registry.register_event(event=ParentTransactionUpdated)
def send_notification_on_transaction_update(context: ParentTransactionUpdated.Context):
    parent_transaction = context.parent_transaction

    def build_notification_for_user(user: User) -> Notification:
        with translation.override(get_language_code_for_user(user)):
            body = _('{editor} just updated a transaction ("{description}")\nHave a look!').format(
                editor=parent_transaction.lastmodified_by.name,
                description=parent_transaction.description,
            )
            head = _("Transaction updated")

        return Notification(
            payload=Notification.Payload(
                head=head,
                body=body,
                click_url=reverse(
                    viewname="transaction:detail",
                    kwargs={"room_slug": parent_transaction.room.slug, "pk": parent_transaction.id},
                ),
            ),
        )

    # If a user, who is not the creditor, updated this transaction, notify the creditor
    if parent_transaction.lastmodified_by != parent_transaction.paid_by:
        build_notification_for_user(parent_transaction.paid_by).send_to_user(parent_transaction.paid_by)

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        # If a user updated this transaction on another ones behalf and is a debtor, do not notify them
        if parent_transaction.lastmodified_by == child_transaction.paid_for:
            continue

        build_notification_for_user(child_transaction.paid_for).send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=ParentTransactionDeleted)
def send_notification_on_child_transaction_deleted(context: ParentTransactionDeleted.Context):
    parent_transaction = context.parent_transaction

    def build_notification_for_user(user: User) -> Notification:
        with translation.override(get_language_code_for_user(user)):
            body = _('{deleter} just deleted a transaction ("{description}")\nHave a look!').format(
                deleter=context.user_who_deleted.name,
                description=parent_transaction.description,
            )
            head = _("Transaction deleted")

        return Notification(
            payload=Notification.Payload(
                head=head,
                body=body,
                click_url=reverse(
                    viewname="transaction:list",
                    kwargs={
                        "room_slug": parent_transaction.room.slug,
                    },
                ),
            ),
        )

    build_notification_for_user(parent_transaction.paid_by).send_to_user(parent_transaction.paid_by)

    for child_transaction in ChildTransaction.objects.filter(parent_transaction_id=parent_transaction.id):
        # If a user updated this transaction on another ones behalf and is a debtor, do not notify them
        if parent_transaction.lastmodified_by == child_transaction.paid_for:
            continue

        build_notification_for_user(child_transaction.paid_for).send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=DebtSettled)
def send_notification_on_debt_settled(context: DebtSettled.Context):
    debt = context.debt

    with translation.override(get_language_code_for_user(debt.creditor)):
        body = _("{debitor} just settled their debt of {amount}{currency} to you").format(
            debitor=debt.debitor,
            amount=debt.value,
            currency=debt.currency.sign,
        )
        head = _("Debt settled")

    Notification(
        payload=Notification.Payload(
            head=head,
            body=body,
            click_url=reverse(viewname="debt:list", kwargs={"room_slug": debt.room.slug}),
        ),
    ).send_to_user(debt.creditor)


@message_registry.register_event(event=UserRemovedFromRoom)
def send_notification_on_user_removed_from_room(context: UserRemovedFromRoom.Context):
    def build_notification_for_user(user: User) -> Notification:
        with translation.override(get_language_code_for_user(user)):
            body = _("{remover} just removed {removed} from {room}").format(
                remover=context.user_requesting_removal.name,
                removed=context.user_to_be_removed.name,
                room=context.room.name,
            )
            head = _("User removed")

        return Notification(
            payload=Notification.Payload(
                head=head,
                body=body,
                click_url=reverse(viewname="account:list", kwargs={"room_slug": context.room.slug}),
            ),
        )

    for user in context.room.users.exclude(id=context.user_requesting_removal.id):
        build_notification_for_user(user).send_to_user(user)
