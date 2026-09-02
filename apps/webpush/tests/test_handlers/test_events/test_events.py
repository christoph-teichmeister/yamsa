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

    def test_send_notification_on_transaction_create_to_debitors_except_for_creator_and_creditor_if_someone_else_created(  # noqa: E501
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

    def test_send_notification_on_transaction_create_body_when_creator_is_payer(
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

        with (
            mock.patch.object(Notification, "send_to_user"),
            mock.patch(
                "apps.webpush.handlers.events.events.Notification",
                wraps=Notification,
            ) as mocked_notification,
        ):
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room)
            )

        body = mocked_notification.call_args.kwargs["payload"].body
        assert body == (
            f"{user.name} logged a payment of {parent_transaction.value}{parent_transaction.currency.sign} "
            f'("{parent_transaction.description}")\n'
            f"Have a look!"
        )

    def test_send_notification_on_transaction_create_body_when_creator_differs_from_payer(
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

        with (
            mock.patch.object(Notification, "send_to_user"),
            mock.patch(
                "apps.webpush.handlers.events.events.Notification",
                wraps=Notification,
            ) as mocked_notification,
        ):
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room)
            )

        expected_body = (
            f"{another_user.name} logged that {user.name} paid "
            f"{parent_transaction.value}{parent_transaction.currency.sign} "
            f'("{parent_transaction.description}")\n'
            f"Have a look!"
        )
        assert mocked_notification.call_args_list
        for call in mocked_notification.call_args_list:
            assert call.kwargs["payload"].body == expected_body

    def test_send_notification_on_transaction_create_localizes_body_per_recipient_language(
        self,
        room,
        user,
        guest_user,
        another_user,
        create_parent_transaction_with_optimisation,
    ):
        room.users.add(another_user)
        guest_user.language = "de"
        guest_user.save(update_fields=["language"])
        user.language = "en"
        user.save(update_fields=["language"])

        with mock.patch.object(CurrentRequestMiddleware, "get_current_user", return_value=another_user):
            parent_transaction, _ = create_parent_transaction_with_optimisation(
                room=room,
                paid_by=user,
                paid_for_tuple=(guest_user, user, another_user),
                parent_transaction_kwargs={"created_by": another_user},
                child_transaction_kwargs={"value": Decimal(10)},
            )

        with (
            mock.patch.object(Notification, "send_to_user") as mocked_send,
            mock.patch(
                "apps.webpush.handlers.events.events.Notification",
                wraps=Notification,
            ) as mocked_notification,
        ):
            send_notification_on_transaction_create(
                context=ParentTransactionCreated.Context(parent_transaction=parent_transaction, room=room)
            )

        recipients = [call.args[0] for call in mocked_send.call_args_list]
        bodies = [call.kwargs["payload"].body for call in mocked_notification.call_args_list]
        body_by_recipient = dict(zip(recipients, bodies, strict=True))

        assert body_by_recipient[guest_user] == (
            f"{another_user.name} hat eingetragen, dass {user.name} "
            f'{parent_transaction.value}{parent_transaction.currency.sign} gezahlt hat ("{parent_transaction.description}")\n'  # noqa: E501
            f"Schau vorbei!"
        )
        assert body_by_recipient[user] == (
            f"{another_user.name} logged that {user.name} paid "
            f"{parent_transaction.value}{parent_transaction.currency.sign} "
            f'("{parent_transaction.description}")\n'
            f"Have a look!"
        )
