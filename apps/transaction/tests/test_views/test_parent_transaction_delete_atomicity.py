from datetime import timedelta
from unittest import mock

import pytest
from django.utils import timezone

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.messages.events.transaction import ParentTransactionDeleted
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.services.transaction_deletion_service import UNDO_WINDOW, TransactionDeletionService
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


FINALISE_MESSAGE = "apps.transaction.services.transaction_deletion_service.handle_message"


def _trash_and_expire(parent: ParentTransaction, user: User) -> None:
    TransactionDeletionService.trash(parent, user=user)
    ParentTransaction.all_objects.filter(pk=parent.pk).update(
        deleted_at=timezone.now() - UNDO_WINDOW - timedelta(seconds=1)
    )


class TestFinaliseExpired:
    def test_the_event_follows_the_deletion(self, room: Room, user: User, guest_user: User) -> None:
        parent, _ = create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        _trash_and_expire(parent, user)
        existed_when_notified = []

        def record(message: ParentTransactionDeleted) -> None:
            existed_when_notified.append(ParentTransaction.all_objects.filter(pk=parent.pk).exists())

        with mock.patch(FINALISE_MESSAGE, side_effect=record):
            TransactionDeletionService.finalise_expired()

        assert existed_when_notified == [False]

    def test_a_failing_delete_leaves_transaction_and_shares_untouched(
        self, room: Room, user: User, guest_user: User
    ) -> None:
        parent, _ = create_parent_transaction_with_optimisation(room=room, paid_by=user, paid_for_tuple=(guest_user,))
        _trash_and_expire(parent, user)

        with (
            mock.patch.object(ParentTransaction, "delete", side_effect=RuntimeError("boom")),
            mock.patch(FINALISE_MESSAGE) as handle_message,
            pytest.raises(RuntimeError),
        ):
            TransactionDeletionService.finalise_expired()

        handle_message.assert_not_called()
        assert ChildTransaction.all_objects.filter(parent_transaction=parent).count() == 1
