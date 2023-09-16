from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.transaction.models import Transaction


class TransactionCreated(Event):
    @dataclass
    class Context:
        transaction: Transaction
