from decimal import Decimal
from unittest import mock

from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.tests.baker_recipes import create_parent_transaction_with_optimisation
from apps.webpush.dataclasses import Notification
from apps.webpush.handlers.events.events import send_notification_on_transaction_create


class EventTestCase(BaseTestSetUp):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.another_user = baker.make_recipe("apps.account.tests.user")

    def test_send_notification_on_transaction_create_to_debitor_if_creditor_is_creator(self):
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.guest_user, self.user),
            parent_transaction_kwargs={"created_by": self.user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        with mock.patch.object(Notification, "send_to_user") as mocked_send:
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=self.room)
            )

            mocked_send.assert_called_once_with(self.guest_user)

    def test_send_notification_on_transaction_create_to_multiple_debitors_if_creditor_is_creator(self):
        self.room.users.add(self.another_user)

        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.guest_user, self.user, self.another_user),
            parent_transaction_kwargs={"created_by": self.user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        with mock.patch.object(Notification, "send_to_user") as mocked_send:
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=self.room)
            )

            mocked_send.assert_any_call(self.guest_user)
            mocked_send.assert_any_call(self.another_user)

            self.assertEqual(mocked_send.call_count, 2)

    def test_send_notification_on_transaction_create_to_debitors_except_for_creator_and_creditor_if_someone_else_created(  # noqa: E501
        self,
    ):
        parent_transaction, _ = create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.guest_user, self.user, self.another_user),
            parent_transaction_kwargs={"created_by": self.another_user},
            child_transaction_kwargs={"value": Decimal(10)},
        )

        with mock.patch.object(Notification, "send_to_user") as mocked_send:
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=self.room)
            )

            mocked_send.assert_any_call(self.guest_user)
            mocked_send.assert_any_call(self.user)

            self.assertEqual(mocked_send.call_count, 2)
