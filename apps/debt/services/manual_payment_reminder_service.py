from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from apps.account.models import User
from apps.debt.models import Debt, ReminderLog
from apps.debt.services.manual_reminder_too_soon_error import ManualReminderTooSoonError
from apps.room.models import Room


class ManualPaymentReminderService:
    """Lets a creditor nudge the debtor of an open debt, at most once per cooldown window."""

    COOLDOWN = timedelta(hours=24)

    @staticmethod
    def can_remind(debt: Debt, creditor: User) -> bool:
        return not debt.settled and debt.creditor_id == creditor.id and not debt.debitor.is_guest

    @classmethod
    def record(cls, debt: Debt, creditor: User) -> ReminderLog:
        """Log a reminder after checking the viewer may chase this debt (PermissionDenied) and the cooldown.

        The caller sends the notifications afterwards, outside any transaction.
        """
        if not cls.can_remind(debt, creditor):
            raise PermissionDenied

        with transaction.atomic():
            # The room row is the lock: two simultaneous clicks must not both pass the window check below.
            Room.objects.select_for_update().get(pk=debt.room_id)

            # Per room, creditor and debitor rather than per Debt row: the optimiser deletes and recreates open
            # debts on every transaction, so a row id would not survive the window.
            last_log = (
                ReminderLog.objects.filter(
                    reminder_type=ReminderLog.ReminderType.MANUAL_DEBT,
                    room_id=debt.room_id,
                    debitor_id=debt.debitor_id,
                    created_by_id=creditor.id,
                    created_at__gt=timezone.now() - cls.COOLDOWN,
                )
                .order_by("-created_at")
                .first()
            )
            if last_log:
                raise ManualReminderTooSoonError(last_log.created_at + cls.COOLDOWN)

            return ReminderLog.objects.create(
                reminder_type=ReminderLog.ReminderType.MANUAL_DEBT,
                recipients=[debt.debitor.email],
                room_id=debt.room_id,
                debitor_id=debt.debitor_id,
                created_by=creditor,
            )
