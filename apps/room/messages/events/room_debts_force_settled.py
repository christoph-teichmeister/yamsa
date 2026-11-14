from dataclasses import dataclass

from apps.account.models import User
from apps.core.event_loop.messages import Event
from apps.room.models import Room


class RoomDebtsForceSettled(Event):
    """A room was closed with open debts, which were marked settled without being paid."""

    @dataclass
    class Context:
        room: Room
        actor: User
        # Debtors and creditors of the debts that were force-settled, captured before the update.
        affected_user_ids: list[int]
