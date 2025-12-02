from decimal import Decimal
from unittest import mock

import pytest
from ambient_toolbox.middleware.current_request import CurrentRequestMiddleware

from apps.account.tests.factories import UserFactory
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.webpush.handlers.events.events import send_notification_on_transaction_create
from apps.webpush.utils import Notification


@pytest.mark.django_db
class TestSendNotificationOnTransactionCreate:
    @pytest.fixture
    def another_user(self):
        return UserFactory()

    def test_send_notification_on_transaction_create_to_debitor_if_creditor_is_creator(
        self,
        room,
        user,
        guest_user,
        create_parent_transaction_with_optimisation,
    ):
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user),
            parent_transaction_kwargs={"created_by": user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        with mock.patch.object(Notification, "send_to_user") as mocked_send:
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room)
            )

            mocked_send.assert_called_once_with(guest_user)

    def test_send_notification_on_transaction_create_to_multiple_debitors_if_creditor_is_creator(
        self,
        room,
        user,
        guest_user,
        another_user,
        create_parent_transaction_with_optimisation,
    ):
        room.users.add(another_user)

        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(guest_user, user, another_user),
            parent_transaction_kwargs={"created_by": user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        with mock.patch.object(Notification, "send_to_user") as mocked_send:
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room)
            )

            mocked_send.assert_any_call(guest_user)
            mocked_send.assert_any_call(another_user)

            assert mocked_send.call_count == 2

    def test_send_notification_on_transaction_create_to_debitors_except_for_creator_and_creditor_if_someone_else_created(
        self,
        room,
        user,
        guest_user,
        another_user,
        create_parent_transaction_with_optimisation,
    ):
        room.users.add(another_user)
        with mock.patch.object(CurrentRequestMiddleware, "get_current_user", return_value=another_user):
            parent_transaction, _ = create_parent_transaction_with_optimisation(
                room=room,
                paid_by=user,
                paid_for_tuple=(guest_user, user, another_user),
                parent_transaction_kwargs={"created_by": another_user},
                child_transaction_kwargs={"value": Decimal(10)},
            )
        with mock.patch.object(Notification, "send_to_user") as mocked_send:
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room)
            )

            mocked_send.assert_any_call(guest_user)
            mocked_send.assert_any_call(user)

            assert mocked_send.call_count == 2, mocked_send.call_args_list
