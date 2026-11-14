from decimal import Decimal

from django.urls import reverse
from django.utils import translation
from django.utils.formats import number_format
from django.utils.translation import gettext as _

from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.account.models import User
from apps.account.utils.language import get_language_code_for_user
from apps.core.event_loop.registry import message_registry
from apps.debt.messages.events.debt_marked_paid import DebtMarkedPaid
from apps.debt.messages.events.debt_payment_rejected import DebtPaymentRejected
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.transaction.messages.events.transaction import (
    ChildTransactionDeleted,
    ParentTransactionCreated,
    ParentTransactionDeleted,
    ParentTransactionUpdated,
    TransactionsImported,
)
from apps.transaction.models import ChildTransaction
from apps.webpush.utils import Notification


def _amount(value: Decimal) -> str:
    """Format for the active language; only meaningful inside the recipient's `translation.override`."""
    return number_format(value, use_l10n=True)


@message_registry.register_event(event=ParentTransactionCreated, atomic=False)
def send_notification_on_transaction_create(context: ParentTransactionCreated.Context) -> None:
    parent_transaction = context.parent_transaction

    def build_notification_for_user(user: User) -> Notification:
        language_code = get_language_code_for_user(user)
        with translation.override(language_code):
            if not parent_transaction.created_by or parent_transaction.created_by == parent_transaction.paid_by:
                body = _('{payer} logged a payment of {amount}{currency} ("{description}")').format(
                    payer=parent_transaction.paid_by.name,
                    amount=_amount(parent_transaction.value),
                    currency=parent_transaction.currency.sign,
                    description=parent_transaction.description,
                )
            else:
                body = _('{creator} logged that {payer} paid {amount}{currency} ("{description}")').format(
                    creator=parent_transaction.created_by.name,
                    payer=parent_transaction.paid_by.name,
                    amount=_amount(parent_transaction.value),
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
        if child_transaction.paid_for in {parent_transaction.created_by, parent_transaction.paid_by}:
            continue

        build_notification_for_user(child_transaction.paid_for).send_to_user(child_transaction.paid_for)


@message_registry.register_event(event=ChildTransactionDeleted, atomic=False)
@message_registry.register_event(event=ParentTransactionUpdated, atomic=False)
def send_notification_on_transaction_update(context: ParentTransactionUpdated.Context) -> None:
    parent_transaction = context.parent_transaction

    def build_notification_for_user(user: User) -> Notification:
        with translation.override(get_language_code_for_user(user)):
            body = _('{editor} just updated a transaction ("{description}")').format(
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


@message_registry.register_event(event=ParentTransactionDeleted, atomic=False)
def send_notification_on_child_transaction_deleted(context: ParentTransactionDeleted.Context) -> None:
    parent_transaction = context.parent_transaction

    def build_notification_for_user(user: User) -> Notification:
        with translation.override(get_language_code_for_user(user)):
            body = _('{deleter} just deleted a transaction ("{description}")').format(
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
                        "room_slug": context.room.slug,
                    },
                ),
            ),
        )

    if parent_transaction.paid_by != context.user_who_deleted:
        build_notification_for_user(parent_transaction.paid_by).send_to_user(parent_transaction.paid_by)

    for debtor in context.debtors:
        # The deleter knows; someone else may have deleted it on the payer's or a debtor's behalf.
        if debtor == context.user_who_deleted:
            continue

        build_notification_for_user(debtor).send_to_user(debtor)


@message_registry.register_event(event=DebtSettled, atomic=False)
def send_notification_on_debt_settled(context: DebtSettled.Context) -> None:
    debt = context.debt
    settled_by_creditor = context.settled_by == debt.creditor
    recipient = debt.debitor if settled_by_creditor else debt.creditor

    with translation.override(get_language_code_for_user(recipient)):
        if settled_by_creditor:
            body = _("{creditor} marked your debt of {amount}{currency} as settled").format(
                creditor=debt.creditor,
                amount=_amount(debt.value),
                currency=debt.currency.sign,
            )
        else:
            body = _("{debitor} just settled their debt of {amount}{currency} to you").format(
                debitor=debt.debitor,
                amount=_amount(debt.value),
                currency=debt.currency.sign,
            )
        head = _("Debt settled")

    Notification(
        payload=Notification.Payload(
            head=head,
            body=body,
            click_url=reverse(viewname="debt:list", kwargs={"room_slug": debt.room.slug}),
        ),
    ).send_to_user(recipient)


@message_registry.register_event(event=DebtMarkedPaid, atomic=False)
def send_notification_on_debt_marked_paid(context: DebtMarkedPaid.Context) -> None:
    debt = context.debt
    with translation.override(get_language_code_for_user(debt.creditor)):
        head = _("Payment to confirm")
        body = _("{debitor} says they paid their debt of {amount}{currency} to you. Please confirm.").format(
            debitor=debt.debitor,
            amount=_amount(debt.value),
            currency=debt.currency.sign,
        )

    Notification(
        payload=Notification.Payload(
            head=head,
            body=body,
            click_url=reverse(viewname="debt:list", kwargs={"room_slug": debt.room.slug}),
        ),
    ).send_to_user(debt.creditor)


@message_registry.register_event(event=DebtPaymentRejected, atomic=False)
def send_notification_on_debt_payment_rejected(context: DebtPaymentRejected.Context) -> None:
    debt = context.debt
    with translation.override(get_language_code_for_user(debt.debitor)):
        head = _("Payment not received")
        body = _("{creditor} did not receive your payment of {amount}{currency}. The debt is open again.").format(
            creditor=debt.creditor,
            amount=_amount(debt.value),
            currency=debt.currency.sign,
        )

    Notification(
        payload=Notification.Payload(
            head=head,
            body=body,
            click_url=reverse(viewname="debt:list", kwargs={"room_slug": debt.room.slug}),
        ),
    ).send_to_user(debt.debitor)


@message_registry.register_event(event=UserRemovedFromRoom, atomic=False)
def send_notification_on_user_removed_from_room(context: UserRemovedFromRoom.Context) -> None:
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


@message_registry.register_event(event=TransactionsImported, atomic=False)
def send_notification_on_transactions_imported(context: TransactionsImported.Context) -> None:
    """One summary notification for the whole import, never one per imported row."""
    room = context.room
    importer = context.triggered_by
    total = context.imported_count + context.settled_count

    for user in room.users.exclude(pk=importer.pk).exclude(is_guest=True):
        with translation.override(get_language_code_for_user(user)):
            head = _("Transactions imported")
            body = _('{importer} imported {count} entries from {source} into "{room}"').format(
                importer=importer.name,
                count=total,
                source=context.source_label,
                room=room.name,
            )

        notification = Notification(
            payload=Notification.Payload(
                head=head,
                body=body,
                click_url=reverse(viewname="transaction:list", kwargs={"room_slug": room.slug}),
            ),
        )
        notification.send_to_user(user)
