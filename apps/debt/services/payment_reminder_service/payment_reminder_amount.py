from dataclasses import dataclass
from decimal import Decimal

from apps.currency.models import Currency


@dataclass(frozen=True)
class PaymentReminderAmount:
    currency: Currency
    amount: Decimal
