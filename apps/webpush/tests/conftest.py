from collections.abc import Callable
from decimal import Decimal

import pytest

from apps.account.models import User
from apps.debt.handlers.events.optimise_debts import calculate_optimised_debts
from apps.room.models import Room
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory
from apps.webpush.services.notification_send_test_service import NotificationSendTestService


@pytest.fixture
def create_parent_transaction_with_optimisation() -> Callable:
    def _create(
        room: Room,
        paid_by: User,
        paid_for_tuple: tuple[User, ...],
        parent_transaction_kwargs: dict | None = None,
        child_transaction_kwargs: dict | None = None,
    ) -> tuple[ParentTransaction, tuple[ChildTransaction, ...]]:
        parent_kwargs = parent_transaction_kwargs or {}
        child_kwargs = child_transaction_kwargs or {}

        parent_transaction = ParentTransactionFactory(
            room=room,
            paid_by=paid_by,
            currency=room.preferred_currency,
            **parent_kwargs,
        )

        children = []
        for paid_for_user in paid_for_tuple:
            child_data = {
                "parent_transaction": parent_transaction,
                "paid_for": paid_for_user,
                "value": Decimal(10),
                **child_kwargs,
            }
            children.append(ChildTransaction.objects.create(**child_data))

        calculate_optimised_debts(ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room))

        return parent_transaction, tuple(children)

    return _create


@pytest.fixture
def outbox() -> NotificationSendTestService:
    """The test push boundary: `TestNotification.send_to_user` appends here instead of calling a push service."""
    service = NotificationSendTestService()
    service.empty()
    return service


@pytest.fixture
def opt_in_to_webpush() -> Callable[..., None]:
    def _opt_in(*users: User) -> None:
        for user in users:
            user.wants_to_receive_webpush_notifications = True
            user.save(update_fields=["wants_to_receive_webpush_notifications"])

    return _opt_in
