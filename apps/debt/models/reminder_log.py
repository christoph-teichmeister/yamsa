from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext_lazy as _


class ReminderLog(CommonInfo):
    class ReminderType(models.TextChoices):
        """TextChoices keeps the recorded reminder type human-readable in historical logs."""

        INACTIVE_DEBT = "inactive_debt", _("Inactive debt reminder")
        INACTIVE_ROOM = "inactive_room", _("Inactive room reminder")
        MANUAL_DEBT = "manual_debt", _("Manual debt reminder")

    reminder_type = models.CharField(
        max_length=50,
        choices=ReminderType.choices,
        default=ReminderType.INACTIVE_DEBT,
    )
    recipients = models.JSONField(default=list)
    # Only set for MANUAL_DEBT: the rate limit counts per room, creditor (created_by) and debitor rather than per
    # Debt row, because the optimiser deletes and recreates open debts on every transaction.
    room = models.ForeignKey("room.Room", null=True, blank=True, on_delete=models.CASCADE, related_name="+")
    debitor = models.ForeignKey("account.User", null=True, blank=True, on_delete=models.CASCADE, related_name="+")

    class Meta:
        verbose_name = _("Reminder log")
        verbose_name_plural = _("Reminder logs")

    def __str__(self) -> str:
        return f"{self.reminder_type} @ {self.created_at.isoformat()}"
