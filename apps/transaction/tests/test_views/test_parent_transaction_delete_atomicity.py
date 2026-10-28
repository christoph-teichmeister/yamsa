from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.messages.events.transaction import ParentTransactionDeleted
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


PARENT_DELETE_MESSAGE = "apps.transaction.views.parent_transaction_delete_view.handle_message"


class TestParentTransactionDelete:
    def test_the_event_follows_the_deletion(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        parent, _ = create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        existed_when_notified = []

        def record(message: ParentTransactionDeleted) -> None:
            existed_when_notified.append(ParentTransaction.objects.filter(pk=parent.pk).exists())

        with mock.patch(PARENT_DELETE_MESSAGE, side_effect=record):
            authenticated_client.post(
                reverse("transaction:parent-transaction-delete", kwargs={"room_slug": room.slug, "pk": parent.pk})
            )

        assert existed_when_notified == [False]

    def test_a_failing_delete_leaves_transaction_and_shares_untouched(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        parent, _ = create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))

        with (
            mock.patch.object(ParentTransaction, "delete", side_effect=RuntimeError("boom")),
            mock.patch(PARENT_DELETE_MESSAGE) as handle_message,
            pytest.raises(RuntimeError),
        ):
            authenticated_client.post(
                reverse("transaction:parent-transaction-delete", kwargs={"room_slug": room.slug, "pk": parent.pk})
            )

        handle_message.assert_not_called()
        assert parent.child_transactions.count() == 1
