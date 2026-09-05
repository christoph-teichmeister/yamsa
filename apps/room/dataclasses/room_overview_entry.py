from dataclasses import dataclass

from apps.room.dataclasses.room_balance import RoomBalance


@dataclass(frozen=True)
class RoomOverviewEntry:
    """One room card on the dashboard."""

    slug: str
    name: str
    description: str
    status: int
    status_label: str
    capitalised_initials: str
    created_by_name: str
    user_is_in_room: bool
    is_closed: bool
    target_url: str
    balances: tuple[RoomBalance, ...]
