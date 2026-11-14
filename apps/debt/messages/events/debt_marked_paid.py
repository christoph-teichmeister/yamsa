from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.debt.models import Debt


class DebtMarkedPaid(Event):
    """The debitor says they paid; the creditor is asked to confirm."""

    @dataclass
    class Context:
        debt: Debt
