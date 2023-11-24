from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.room.models import Room
from apps.transaction.models import ParentTransaction


class ParentTransactionCreated(Event):
    @dataclass
    class Context:
        parent_transaction: ParentTransaction
        room: Room


class ParentTransactionUpdated(Event):
    @dataclass
    class Context:
        parent_transaction: ParentTransaction
        room: Room


class AnyTransactionDeleted(Event):
    @dataclass
    class Context:
        parent_transaction = None
        room: Room
