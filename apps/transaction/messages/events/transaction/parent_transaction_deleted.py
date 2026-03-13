from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Event
from apps.room.models import Room
from apps.transaction.models import ParentTransaction


class ParentTransactionDeleted(Event):
    @dataclass
    class Context:
        parent_transaction: ParentTransaction
        room: Room
        user_who_deleted: User
