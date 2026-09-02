from decimal import Decimal
from unittest import mock

import pytest

from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.account.tests.factories import UserFactory
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.debt.models import Debt
from apps.transaction.messages.events.transaction import ParentTransactionDeleted, ParentTransactionUpdated
from apps.webpush.handlers.events.events import (
    send_notification_on_child_transaction_deleted,
    send_notification_on_debt_settled,
    send_notification_on_transaction_update,
    send_notification_on_user_removed_from_room,
)
from apps.webpush.utils import Notification


@pytest.mark.django_db
def test_send_notification_on_transaction_update_localizes_body_per_recipient_language(
    room,
    user,
    guest_user,
    create_parent_transaction_with_optimisation,
):
    another_user = UserFactory(language="de")
    room.users.add(another_user)

    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room,
        paid_by=user,
        paid_for_tuple=(guest_user, another_user),
        parent_transaction_kwargs={"created_by": user, "lastmodified_by": user},
        child_transaction_kwargs={"value": Decimal(10)},
    )

    with (
        mock.patch.object(Notification, "send_to_user") as mocked_send,
        mock.patch("apps.webpush.handlers.events.events.Notification", wraps=Notification) as mocked_notification,
    ):
        send_notification_on_transaction_update(
            context=ParentTransactionUpdated.Context(parent_transaction=parent_transaction, room=room)
        )

    recipients = [call.args[0] for call in mocked_send.call_args_list]
    bodies = [call.kwargs["payload"].body for call in mocked_notification.call_args_list]
    body_by_recipient = dict(zip(recipients, bodies, strict=True))

    assert body_by_recipient[guest_user] == (
        f'{user.name} just updated a transaction ("{parent_transaction.description}")\nHave a look!'
    )
    assert body_by_recipient[another_user] == (
        f'{user.name} hat eine Transaktion aktualisiert ("{parent_transaction.description}")\nSchau vorbei!'
    )


@pytest.mark.django_db
def test_send_notification_on_child_transaction_deleted_localizes_body_per_recipient_language(
    room,
    user,
    guest_user,
    create_parent_transaction_with_optimisation,
):
    another_user = UserFactory(language="de")
    room.users.add(another_user)

    parent_transaction, _ = create_parent_transaction_with_optimisation(
        room=room,
        paid_by=user,
        paid_for_tuple=(guest_user, another_user),
        parent_transaction_kwargs={"created_by": user, "lastmodified_by": user},
        child_transaction_kwargs={"value": Decimal(10)},
    )

    with (
        mock.patch.object(Notification, "send_to_user") as mocked_send,
        mock.patch("apps.webpush.handlers.events.events.Notification", wraps=Notification) as mocked_notification,
    ):
        send_notification_on_child_transaction_deleted(
            context=ParentTransactionDeleted.Context(
                parent_transaction=parent_transaction, room=room, user_who_deleted=user
            )
        )

    recipients = [call.args[0] for call in mocked_send.call_args_list]
    bodies = [call.kwargs["payload"].body for call in mocked_notification.call_args_list]
    body_by_recipient = dict(zip(recipients, bodies, strict=True))

    assert body_by_recipient[guest_user] == (
        f'{user.name} just deleted a transaction ("{parent_transaction.description}")\nHave a look!'
    )
    assert body_by_recipient[another_user] == (
        f'{user.name} hat eine Transaktion gelöscht ("{parent_transaction.description}")\nSchau vorbei!'
    )


@pytest.mark.django_db
def test_send_notification_on_debt_settled_localizes_body_to_creditor_language(room, user):
    creditor = UserFactory(language="de")
    debitor = user

    debt = Debt.objects.create(
        debitor=debitor,
        creditor=creditor,
        room=room,
        currency=room.preferred_currency,
        value=Decimal("10"),
    )

    with (
        mock.patch.object(Notification, "send_to_user") as mocked_send,
        mock.patch("apps.webpush.handlers.events.events.Notification", wraps=Notification) as mocked_notification,
    ):
        send_notification_on_debt_settled(context=DebtSettled.Context(debt=debt))

    mocked_send.assert_called_once_with(creditor)
    body = mocked_notification.call_args.kwargs["payload"].body
    head = mocked_notification.call_args.kwargs["payload"].head
    assert head == "Schuld beglichen"
    assert body == f"{debitor} hat seine Schuld von {debt.value}{debt.currency.sign} bei dir beglichen"


@pytest.mark.django_db
def test_send_notification_on_user_removed_from_room_localizes_body_per_recipient_language(room, user, guest_user):
    another_user = UserFactory(language="de")
    room.users.add(another_user)
    remover = user
    removed = guest_user

    with (
        mock.patch.object(Notification, "send_to_user") as mocked_send,
        mock.patch("apps.webpush.handlers.events.events.Notification", wraps=Notification) as mocked_notification,
    ):
        send_notification_on_user_removed_from_room(
            context=UserRemovedFromRoom.Context(room=room, user_to_be_removed=removed, user_requesting_removal=remover)
        )

    recipients = [call.args[0] for call in mocked_send.call_args_list]
    bodies = [call.kwargs["payload"].body for call in mocked_notification.call_args_list]
    body_by_recipient = dict(zip(recipients, bodies, strict=True))

    assert body_by_recipient[guest_user] == f"{remover.name} just removed {removed.name} from {room.name}"
    assert body_by_recipient[another_user] == f"{remover.name} hat {removed.name} aus {room.name} entfernt"
