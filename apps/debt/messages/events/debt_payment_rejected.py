from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.debt.models import Debt


class DebtPaymentRejected(Event):
    """The creditor says the payment never arrived; the debt is open again."""

    @dataclass
    class Context:
        debt: Debt
