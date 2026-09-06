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

    @property
    def is_balanced(self) -> bool:
        """Both sides cancel out, yet the underlying debts are still open and payable.

        Distinct from a room with no open debts at all, which yields no RoomBalance.
        """
        return self.net_amount == Decimal("0")
