from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from apps.room.dataclasses.attention_rank import AttentionRank
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
    balances: tuple[RoomBalance, ...]

    @property
    def user_owes(self) -> bool:
        """True as soon as the user owes in any currency of this room.

        A room owing in one currency and receiving in another counts as owing: paying is the
        obligation the user cannot postpone, so it decides how the room is ranked and coloured.
        """
        return any(balance.user_owes for balance in self.balances)

    @property
    def user_gets_back(self) -> bool:
        return not self.user_owes and any(balance.user_gets_back for balance in self.balances)

    @property
    def attention_rank(self) -> AttentionRank:
        if self.user_owes:
            return AttentionRank.OWING
        if self.user_gets_back:
            return AttentionRank.RECEIVING
        if self.balances:
            return AttentionRank.BALANCED
        return AttentionRank.SETTLED

    @property
    def ranking_amount(self) -> Decimal:
        """The largest open amount of the room, for ordering only - never for display or arithmetic.

        Amounts of different currencies are incomparable without exchange rates, so this ranks
        rooms rather than measuring them: it only ever decides which of two cards sits higher.
        """
        return max((balance.absolute_amount for balance in self.balances), default=Decimal("0"))
