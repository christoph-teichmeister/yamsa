from dataclasses import dataclass

from apps.core.event_loop.messages import Event
from apps.debt.models import Debt


class DebtSettled(Event):
    @dataclass
    class Context:
        debt: Debt
