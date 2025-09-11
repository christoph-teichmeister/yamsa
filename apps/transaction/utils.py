# apps/core/money.py
from decimal import ROUND_HALF_UP, Decimal


def split_amount_exact(total: Decimal, shares: int) -> list[Decimal]:
    """
    Split total into `shares` Decimal values that sum exactly to total.
    Rounds each share to 0.01 using ROUND_HALF_UP and distributes remainder starting at index 0.
    """
    if shares <= 0:
        error_message = "shares must be > 0"
        raise ValueError(error_message)

    unit = Decimal("0.01")
    per = (total / Decimal(shares)).quantize(unit, rounding=ROUND_HALF_UP)
    result = [per] * shares
    remainder = total - sum(result)

    # remainder will be a small Decimal like 0.01, -0.01, etc.
    i = 0
    step = unit if remainder > 0 else -unit
    while remainder != Decimal("0.00"):
        result[i] = (result[i] + step).quantize(unit, rounding=ROUND_HALF_UP)
        remainder = total - sum(result)
        i = (i + 1) % shares

    return result
