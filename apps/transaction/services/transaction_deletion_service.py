from datetime import timedelta

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.room.models import Room
from apps.transaction.constants import DELETE_UNDO_GRACE_SECONDS, DELETE_UNDO_SECONDS
from apps.transaction.messages.events.transaction import (
    ParentTransactionDeleted,
    ParentTransactionRestored,
    ParentTransactionTrashed,
)
from apps.transaction.models import ParentTransaction

UNDO_WINDOW = timedelta(seconds=DELETE_UNDO_SECONDS + DELETE_UNDO_GRACE_SECONDS)


class TransactionDeletionService:
    """Deleting a transaction is a soft delete first, so it can be undone for a few seconds.

    `trash` hides the transaction from every sum and recalculates the debts, but tells nobody.
    `restore` undoes that inside the window. `finalise_expired` deletes the rows for good once the
    window has passed and only then fires `ParentTransactionDeleted`, which is what writes the news
    item and sends the push notifications. Nothing runs on a timer: it is called on the next visit
    to the room's transactions and by the `purge_deleted_transactions` command.
    """

    @staticmethod
    def trash(parent_transaction: ParentTransaction, *, user: User) -> None:
        # update() rather than save(): the model's full_clean has no business in a delete.
        ParentTransaction.objects.filter(pk=parent_transaction.pk).update(deleted_at=timezone.now(), deleted_by=user)
        # Events run after the write has committed, never inside an atomic block (#333).
        handle_message(
            ParentTransactionTrashed(
                context_data={"parent_transaction": parent_transaction, "room": parent_transaction.room}
            )
        )

    @staticmethod
    def restore(*, pk: int, room: Room) -> ParentTransaction | None:
        """Bring a deleted transaction back; None when it is gone or its window has passed."""
        with transaction.atomic():
            # The row lock orders this against finalise_expired deleting the same row.
            restorable = (
                ParentTransaction.all_objects.select_for_update()
                .filter(pk=pk, room=room, deleted_at__gte=timezone.now() - UNDO_WINDOW)
                .first()
            )
            if restorable is None:
                return None
            ParentTransaction.all_objects.filter(pk=pk).update(deleted_at=None, deleted_by=None)

        handle_message(ParentTransactionRestored(context_data={"parent_transaction": restorable, "room": room}))
        return restorable

    @staticmethod
    def expired(room: Room | None = None) -> QuerySet[ParentTransaction]:
        expired = ParentTransaction.all_objects.filter(deleted_at__lt=timezone.now() - UNDO_WINDOW)
        return expired.filter(room=room) if room else expired

    @classmethod
    def finalise_expired(cls, room: Room | None = None) -> int:
        """Delete every transaction whose window has passed; returns how many."""
        finalised = 0
        for pk in cls.expired(room).values_list("pk", flat=True):
            with transaction.atomic():
                # of=("self",): deleted_by is a nullable join, and PostgreSQL refuses to lock the
                # nullable side of an outer join (SQLite, which the tests use, ignores the lock).
                row = (
                    cls.expired()
                    .select_for_update(of=("self",))
                    .filter(pk=pk)
                    .select_related("room", "currency", "deleted_by")
                ).first()
                if row is None:
                    continue
                # Nobody to name when the deleter's account is gone, so then nobody is told.
                context = (
                    ParentTransactionDeleted.context_before_deletion(row, user_who_deleted=row.deleted_by)
                    if row.deleted_by
                    else None
                )
                row.delete()
            finalised += 1
            if context:
                handle_message(ParentTransactionDeleted(context_data=context))
        return finalised
