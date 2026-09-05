from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RoomBalance:
    """A user's open balance in one room, for one currency.

    The project has no exchange rates, so a room with transactions in several currencies
    yields one RoomBalance per currency and they must never be summed up.
    """

    currency_sign: str
    owed_by_user: Decimal
    owed_to_user: Decimal

    @property
    def net_amount(self) -> Decimal:
        return self.owed_to_user - self.owed_by_user

    @property
    def absolute_amount(self) -> Decimal:
        return abs(self.net_amount)

    @property
    def user_owes(self) -> bool:
        return self.net_amount < 0


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
