from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.account.models import User
from apps.currency.models import Currency
from apps.debt.models import Debt, ReminderLog
from apps.mail.services.payment_reminder_mail_service import PaymentReminderEmailService
from apps.room.models import Room


@dataclass(frozen=True)
class PaymentReminderAmount:
    currency: Currency
    amount: Decimal


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


class PaymentReminderService:
    """Collect overdue debts and notify affected users once per heartbeat window."""

    REMINDER_TYPE = ReminderLog.ReminderType.INACTIVE_DEBT
    HEARTBEAT_INTERVAL = timedelta(days=30)  # Approximate monthly cadence for reminders.

    def __init__(self, *, now: datetime | None = None):
        """Set up a timestamp window that determines which rooms count as inactive."""
        self.now = now or timezone.now()
        # Rooms older than this threshold are eligible for payment nudges.
        self.threshold = self.now - timedelta(days=settings.INACTIVITY_REMINDER_DAYS)

    def run(self) -> list[PaymentReminderCandidate]:
        """Send an email to every candidate that still owes a balance in an inactive room."""

        if not settings.INACTIVITY_REMINDER_ENABLED:
            return []

        candidates = self._collect_candidates()
        recipients: list[str] = []
        for candidate in candidates:
            PaymentReminderEmailService(
                recipient=candidate.user,
                room_name=candidate.room.name,
                amount_summary=candidate.amount_summary(),
                inactivity_days=settings.INACTIVITY_REMINDER_DAYS,
                payment_link=self._build_payment_link(candidate.room),
            ).process()
            recipients.append(candidate.user.email)

        # Keep a log of every reminder wave along with the affected recipients.
        ReminderLog.objects.create(
            reminder_type=self.REMINDER_TYPE,
            recipients=sorted(set(recipients)),
        )

        return candidates

    def run_if_due(self) -> list[PaymentReminderCandidate]:
        """Execute `run` only when the heartbeat window allows another reminder wave."""
        if not self.should_run():
            return []
        return self.run()

    def should_run(self) -> bool:
        """Avoid sending reminders more often than the heartbeat interval."""
        if not settings.INACTIVITY_REMINDER_ENABLED:
            return False

        last_log = ReminderLog.objects.filter(reminder_type=self.REMINDER_TYPE).order_by("-created_at").first()

        if not last_log:
            return True

        return last_log.created_at + self.HEARTBEAT_INTERVAL <= self.now

    def _collect_candidates(self) -> list[PaymentReminderCandidate]:
        """Gather users who are behind on payments in rooms that have gone quiet."""
        rooms = (
            Room.objects.annotate_last_transaction_lastmodified_at_date()
            .filter(status=Room.StatusChoices.OPEN)
            .filter(debts__settled=False)
            .filter(
                Q(last_transaction_created_at_date__lt=self.threshold)
                | Q(last_transaction_created_at_date__isnull=True)
            )
            .distinct()
        )

        candidates: list[PaymentReminderCandidate] = []
        for room in rooms:
            last_activity = getattr(room, "last_transaction_created_at_date", None)
            builders = self._builders_for_room(room)
            for builder in builders:
                candidates.append(builder.build(last_activity))

        return candidates

    def _builders_for_room(self, room: Room) -> list[_PaymentReminderBuilder]:
        """Accumulate debt totals per user so each recipient receives a single email."""
        debts = Debt.objects.filter(room=room, settled=False).select_related("debitor", "currency")
        builders: dict[int, _PaymentReminderBuilder] = {}
        for debt in debts:
            if debt.debitor.is_guest:
                continue
            if not debt.debitor.wants_to_receive_payment_reminders:
                continue

            builder = builders.get(debt.debitor_id)
            if not builder:
                builder = _PaymentReminderBuilder(user=debt.debitor, room=room)
                builders[debt.debitor_id] = builder

            builder.add(debt)

        return list(builders.values())

    @staticmethod
    def _build_payment_link(room: Room) -> str:
        """Generate a room-specific URL so recipients can settle debts right away."""
        backend = settings.BACKEND_URL.rstrip("/")
        return f"{backend}{reverse('debt:list', kwargs={'room_slug': room.slug})}"
