from datetime import datetime

from apps.account.models import User
from apps.debt.models import Debt
from apps.room.models import Room

from .payment_reminder_amount import PaymentReminderAmount
from .payment_reminder_candidate import PaymentReminderCandidate


class _PaymentReminderBuilder:
    def __init__(self, user: User, room: Room):
        self.user = user
        self.room = room
        self._amounts: dict[int, PaymentReminderAmount] = {}

    def add(self, debt: Debt):
        currency_id = debt.currency_id
        current = self._amounts.get(currency_id)
        if current:
            self._amounts[currency_id] = PaymentReminderAmount(
                currency=current.currency,
                amount=current.amount + debt.value,
            )
        else:
            self._amounts[currency_id] = PaymentReminderAmount(
                currency=debt.currency,
                amount=debt.value,
            )

    def build(self, last_activity_at: datetime | None) -> PaymentReminderCandidate:
        amounts = tuple(sorted(self._amounts.values(), key=lambda amount: amount.currency.code))
        return PaymentReminderCandidate(
            user=self.user,
            room=self.room,
            last_activity_at=last_activity_at,
            amounts=amounts,
        )
