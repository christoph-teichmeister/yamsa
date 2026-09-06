from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CurrencyTotal:
    """What the user owes and is owed across all their open rooms, in one currency.

    Built from each room's *net* balance, never from the gross debts: a room where both sides
    cancel out contributes nothing, and the two sides stay separate because they are not the
    same obligation - the user has to pay ``owed_by_user`` and can only hope for
    ``owed_to_user``.

    Instances are grouped by ``currency_id``, not by ``currency_sign``: Currency has no unique
    constraint on sign, so USD and CAD both use "$" and would otherwise collapse into one sum.
    """

    currency_id: int
    currency_sign: str
    owed_by_user: Decimal
    owed_to_user: Decimal
