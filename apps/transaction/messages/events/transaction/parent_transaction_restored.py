from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.room.models import Room
from apps.transaction.models import ParentTransaction


class ParentTransactionRestored(Event):
    """Sent when a delete is undone: the transaction counts in the room's debts again."""

    @dataclass
    class Context:
        parent_transaction: ParentTransaction
        room: Room
