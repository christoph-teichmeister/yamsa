from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.room.models import Room
from apps.transaction.models import ParentTransaction


class ParentTransactionTrashed(Event):
    """Sent when a transaction enters its undo window: gone from every sum, but not yet deleted.

    Only the debts react. Members hear of the deletion with `ParentTransactionDeleted`, once the
    window has passed, so an undone delete never reaches anybody.
    """

    @dataclass
    class Context:
        parent_transaction: ParentTransaction
        room: Room
