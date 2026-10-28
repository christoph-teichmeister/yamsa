from decimal import Decimal
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.messages.events.transaction import ChildTransactionDeleted, ParentTransactionDeleted
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


CHILD_DELETE_MESSAGE = "apps.transaction.views.child_transaction_delete_view.handle_message"


class TestChildTransactionDelete:
    def test_removing_one_of_several_shares_returns_to_the_edit_form(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        parent, (_, guest_share) = create_parent_transaction_with_optimisation(
            room=room, paid_by=user, paid_for_tuple=(user, guest_user)
        )

        with mock.patch(CHILD_DELETE_MESSAGE) as handle_message:
            response = authenticated_client.post(
                reverse("transaction:child-transaction-delete", kwargs={"room_slug": room.slug, "pk": guest_share.pk})
            )

        assert response.url == reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": parent.pk})
        assert isinstance(handle_message.call_args.args[0], ChildTransactionDeleted)

    def test_removing_the_last_share_deletes_the_transaction_and_returns_to_the_list(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        parent, (share,) = create_parent_transaction_with_optimisation(
            room=room, paid_by=user, paid_for_tuple=(guest_user,)
        )
        existed_when_notified = []

        def record(message: ParentTransactionDeleted) -> None:
            existed_when_notified.append(ParentTransaction.objects.filter(pk=parent.pk).exists())

        with mock.patch(CHILD_DELETE_MESSAGE, side_effect=record):
            response = authenticated_client.post(
                reverse("transaction:child-transaction-delete", kwargs={"room_slug": room.slug, "pk": share.pk})
            )

        assert response.url == reverse("transaction:list", kwargs={"room_slug": room.slug})
        assert existed_when_notified == [False]
        assert not ChildTransaction.objects.filter(pk=share.pk).exists()

    def test_a_failure_while_removing_a_share_keeps_the_value_with_the_deleted_share(
        self, authenticated_client: Client, room: Room, user: User, guest_user: User
    ) -> None:
        _, (user_share, guest_share) = create_parent_transaction_with_optimisation(
            room=room, paid_by=user, paid_for_tuple=(user, guest_user)
        )

        with (
            mock.patch.object(ChildTransaction, "delete", side_effect=RuntimeError("boom")),
            mock.patch(CHILD_DELETE_MESSAGE) as handle_message,
            pytest.raises(RuntimeError),
        ):
            authenticated_client.post(
                reverse("transaction:child-transaction-delete", kwargs={"room_slug": room.slug, "pk": guest_share.pk})
            )

        handle_message.assert_not_called()
        user_share.refresh_from_db()
        assert user_share.value == Decimal(13)
