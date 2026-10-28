from collections.abc import Callable
from decimal import Decimal

import pytest

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.models import Room
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.webpush.handlers.events.events import send_notification_on_transaction_create
from apps.webpush.services.notification_send_test_service import NotificationSendTestService


@pytest.mark.django_db
class TestSendNotificationOnTransactionCreate:
    @pytest.fixture
    def another_user(self) -> User:
        return UserFactory()

    @pytest.fixture(autouse=True)
    def _setup(
        self,
        outbox: NotificationSendTestService,
        opt_in_to_webpush: Callable[..., None],
        user: User,
        guest_user: User,
        another_user: User,
    ) -> None:
        self.outbox = outbox
        opt_in_to_webpush(user, guest_user, another_user)

    def _run(self, room: Room, parent_transaction: object) -> dict[User, str]:
        send_notification_on_transaction_create(
            context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room)
        )
        return {notification.recipient: notification.payload.body for notification in self.outbox.all()}

    def test_send_notification_on_transaction_create_to_debitor_if_creditor_is_creator(
        self,
        room: Room,
        user: User,
        guest_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user),
            parent_transaction_kwargs={"created_by": user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        bodies = self._run(room, parent_transaction)

        assert list(bodies) == [guest_user]

    def test_send_notification_on_transaction_create_to_multiple_debitors_if_creditor_is_creator(
        self,
        room: Room,
        user: User,
        guest_user: User,
        another_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        room.users.add(another_user)

        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user, another_user),
            parent_transaction_kwargs={"created_by": user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        bodies = self._run(room, parent_transaction)

        assert set(bodies) == {guest_user, another_user}
        assert len(self.outbox.all()) == 2

    def test_send_notification_on_transaction_create_to_debitors_except_creator_and_creditor_if_someone_else_created(
        self,
        room: Room,
        user: User,
        guest_user: User,
        another_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        room.users.add(another_user)
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user, another_user),
            parent_transaction_kwargs={"created_by": another_user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        bodies = self._run(room, parent_transaction)

        assert set(bodies) == {guest_user, user}
        assert len(self.outbox.all()) == 2, bodies

    def test_send_notification_on_transaction_create_body_when_creator_is_payer(
        self,
        room: Room,
        user: User,
        guest_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user),
            parent_transaction_kwargs={"created_by": user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        body = self._run(room, parent_transaction)[guest_user]

        assert body == (
            f"{user.name} logged a payment of {parent_transaction.value}{parent_transaction.currency.sign} "
            f'("{parent_transaction.description}")'
        )

    def test_send_notification_on_transaction_create_body_when_creator_differs_from_payer(
        self,
        room: Room,
        user: User,
        guest_user: User,
        another_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        room.users.add(another_user)
        user.language = "en"
        user.save(update_fields=["language"])
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user, another_user),
            parent_transaction_kwargs={"created_by": another_user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        body = self._run(room, parent_transaction)[user]

        assert body == (
            f"{another_user.name} logged that {user.name} paid "
            f"{parent_transaction.value}{parent_transaction.currency.sign} "
            f'("{parent_transaction.description}")'
        )

    def test_send_notification_on_transaction_create_localizes_body_per_recipient_language(
        self,
        room: Room,
        user: User,
        guest_user: User,
        another_user: User,
        create_parent_transaction_with_optimisation: Callable,
    ) -> None:
        room.users.add(another_user)
        guest_user.language = "de"
        guest_user.save(update_fields=["language"])
        user.language = "en"
        user.save(update_fields=["language"])

        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user, another_user),
            parent_transaction_kwargs={"created_by": another_user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        body_by_recipient = self._run(room, parent_transaction)

        assert body_by_recipient[guest_user] == (
            f"{another_user.name} hat eingetragen, dass {user.name} "
            f"{parent_transaction.value}{parent_transaction.currency.sign} gezahlt hat "
            f'("{parent_transaction.description}")'
        )
        assert body_by_recipient[user] == (
            f"{another_user.name} logged that {user.name} paid "
            f"{parent_transaction.value}{parent_transaction.currency.sign} "
            f'("{parent_transaction.description}")'
        )
