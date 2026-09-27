from dataclasses import dataclass
from decimal import Decimal

from apps.account.models import User
from apps.core.event_loop.messages import Event
from apps.room.models import Room
from apps.transaction.models import ParentTransaction


class ParentTransactionDeleted(Event):
    """Sent once a transaction and all its shares are gone from the database.

    Not before: the debts are recalculated from what is left, so a handler running while the shares
    still exist would count them. `parent_transaction` is therefore the deleted instance - its own
    fields still read, but nothing reached through its primary key (`value`, the shares) does. What
    the handlers need from those is carried along instead; build the context with
    `context_before_deletion()` while the transaction still exists.
    """

    @dataclass
    class Context:
        parent_transaction: ParentTransaction
        room: Room
        user_who_deleted: User
        amount: Decimal
        debtors: tuple[User, ...]

    @staticmethod
    def context_before_deletion(parent_transaction: ParentTransaction, *, user_who_deleted: User) -> dict:
        return {
            "parent_transaction": parent_transaction,
            "room": parent_transaction.room,
            "user_who_deleted": user_who_deleted,
            "amount": parent_transaction.value,
            "debtors": tuple(
                child_transaction.paid_for
                for child_transaction in parent_transaction.child_transactions.select_related("paid_for")
            ),
        }
