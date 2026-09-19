from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from apps.room.dataclasses.room_balance import RoomBalance
from apps.room.room_seal import seal_icon, seal_tilt_deg


@dataclass(frozen=True)
class RoomOverviewEntry:
    """One room card on the dashboard."""

    slug: UUID
    name: str
    description: str
    status_label: str
    capitalised_initials: str
    created_by_name: str
    user_is_in_room: bool
    is_closed: bool
    target_url: str
    last_activity_at: datetime
    # None for a room without transactions - it has no last transaction to name, while
    # last_activity_at falls back to the room's own timestamp so it can still be ordered.
    last_transaction_at: datetime | None
    balances: tuple[RoomBalance, ...]

    @property
    def meta_text(self) -> str:
        """The card's secondary line: who owns a room the user is not in, else its description."""
        return self.created_by_name if not self.user_is_in_room else self.description

    @property
    def seal_icon(self) -> str:
        """The room's signature icon - stable per room, not per render, picked off its slug."""
        return seal_icon(self.slug)

    @property
    def seal_tilt_deg(self) -> int:
        """A small stable tilt for the seal, so it reads as stamped rather than centred art."""
        return seal_tilt_deg(self.slug)
