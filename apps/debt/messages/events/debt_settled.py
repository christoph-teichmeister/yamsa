from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Event
from apps.debt.models import Debt


class DebtSettled(Event):
    @dataclass
    class Context:
        debt: Debt
        # Who pressed the button; the other party of the debt is the one to tell. None counts as the debitor.
        settled_by: User | None = None
