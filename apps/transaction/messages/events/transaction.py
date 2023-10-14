from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.transaction.models import ParentTransaction


class ParentTransactionCreated(Event):
    @dataclass
    class Context:
        parent_transaction: ParentTransaction
