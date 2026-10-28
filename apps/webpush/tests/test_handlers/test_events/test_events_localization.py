from collections.abc import Callable
from decimal import Decimal

import pytest

from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.debt.messages.events.debt_settled import DebtSettled
from apps.debt.models import Debt
from apps.room.models import Room
from apps.transaction.messages.events.transaction import ParentTransactionDeleted, ParentTransactionUpdated
from apps.webpush.handlers.events.events import (
    send_notification_on_child_transaction_deleted,
    send_notification_on_debt_settled,
    send_notification_on_transaction_update,
    send_notification_on_user_removed_from_room,
)
from apps.webpush.services.notification_send_test_service import NotificationSendTestService


@pytest.mark.django_db
class TestNotificationLocalization:
    @pytest.fixture(autouse=True)
    def _setup(self, outbox: NotificationSendTestService, opt_in_to_webpush: Callable[..., None]) -> None:
        self.outbox = outbox
        self.opt_in = opt_in_to_webpush

    def _bodies(self) -> dict[User, str]:
        return {notification.recipient: notification.payload.body for notification in self.outbox.all()}

    def test_transaction_update_localizes_body_per_recipient_language(
        self,
        room: Room,
        user: User,
        guest_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        another_user = UserFactory(language="de")
        room.users.add(another_user)
        self.opt_in(user, guest_user, another_user)
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, another_user),
            parent_transaction_kwargs={"created_by": user, "lastmodified_by": user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        send_notification_on_transaction_update(
            context=ParentTransactionUpdated.Context(parent_transaction=parent_transaction, room=room)
        )

        bodies = self._bodies()
        assert bodies[guest_user] == f'{user.name} just updated a transaction ("{parent_transaction.description}")'
        assert bodies[another_user] == (
            f'{user.name} hat eine Transaktion aktualisiert ("{parent_transaction.description}")'
        )

    def test_child_transaction_deleted_localizes_body_per_recipient_language(
        self,
        room: Room,
        user: User,
        guest_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        another_user = UserFactory(language="de")
        room.users.add(another_user)
        self.opt_in(user, guest_user, another_user)
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, another_user),
            parent_transaction_kwargs={"created_by": user, "lastmodified_by": user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        send_notification_on_child_transaction_deleted(
            context=ParentTransactionDeleted(
                context_data=ParentTransactionDeleted.context_before_deletion(parent_transaction, user_who_deleted=user)
            ).Context
        )

        bodies = self._bodies()
        assert bodies[guest_user] == f'{user.name} just deleted a transaction ("{parent_transaction.description}")'
        assert bodies[another_user] == (
            f'{user.name} hat eine Transaktion gelöscht ("{parent_transaction.description}")'
        )

    def test_debt_settled_localizes_body_to_creditor_language(self, room: Room, user: User) -> None:
        creditor = UserFactory(language="de")
        self.opt_in(creditor)
        debt = Debt.objects.create(
            debitor=user,
            creditor=creditor,
            room=room,
            currency=room.preferred_currency,
            value=Decimal(10),
        )

        send_notification_on_debt_settled(context=DebtSettled.Context(debt=debt))

        [notification] = self.outbox.all()
        assert notification.recipient == creditor
        assert notification.payload.head == "Schuld beglichen"
        assert (
            notification.payload.body
            == f"{user} hat seine Schuld von {debt.value}{debt.currency.sign} bei dir beglichen"
        )

    def test_user_removed_from_room_localizes_body_per_recipient_language(
        self, room: Room, user: User, guest_user: User
    ) -> None:
        another_user = UserFactory(language="de")
        room.users.add(another_user)
        self.opt_in(guest_user, another_user)

        send_notification_on_user_removed_from_room(
            context=UserRemovedFromRoom.Context(room=room, user_to_be_removed=guest_user, user_requesting_removal=user)
        )

        bodies = self._bodies()
        assert bodies[guest_user] == f"{user.name} just removed {guest_user.name} from {room.name}"
        assert bodies[another_user] == f"{user.name} hat {guest_user.name} aus {room.name} entfernt"
