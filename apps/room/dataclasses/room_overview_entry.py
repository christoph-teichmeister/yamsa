from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from apps.room.dataclasses.room_balance import RoomBalance


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
    balances: tuple[RoomBalance, ...]
