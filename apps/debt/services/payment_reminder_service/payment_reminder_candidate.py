from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from apps.account.models import User
from apps.currency.models import Currency
from apps.debt.services.payment_reminder_service.payment_reminder_amount import PaymentReminderAmount
from apps.room.models import Room


@dataclass(frozen=True)
class PaymentReminderCandidate:
    user: User
    room: Room
    last_activity_at: datetime | None
    amounts: tuple[PaymentReminderAmount, ...]

    def amount_summary(self) -> str:
        return ", ".join(self._format_amount(amount.currency, amount.amount) for amount in self.amounts)

    @staticmethod
    def _format_amount(currency: Currency, amount: Decimal) -> str:
        quantized = amount.quantize(Decimal("0.01"))
        sign = currency.sign or currency.code.upper()

        return f"{sign}{quantized}"
