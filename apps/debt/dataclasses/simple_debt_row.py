from dataclasses import dataclass
from decimal import Decimal

from apps.account.models import User
from apps.currency.models import Currency


@dataclass(frozen=True)
class SimpleDebtRow:
    """One unoptimised debt, shaped like a Debt row so both display modes share the row template.

    ``settled`` is always False: these rows are derived from transactions and carry no settlement
    state of their own, which is why they must never offer a settle or PayPal action.
    """

    debitor: User
    creditor: User
    value: Decimal
    currency: Currency
    viewer_is_debitor: bool
    viewer_is_creditor: bool
    settled: bool = False
