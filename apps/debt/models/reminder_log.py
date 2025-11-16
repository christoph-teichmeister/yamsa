from ambient_toolbox.models import CommonInfo
from django.db import models


class ReminderLog(CommonInfo):
    class ReminderType(models.TextChoices):
        """TextChoices keeps the recorded reminder type human-readable in historical logs."""

        INACTIVE_DEBT = "inactive_debt", "Inactive debt reminder"
        INACTIVE_ROOM = "inactive_room", "Inactive room reminder"

    reminder_type = models.CharField(
        max_length=50,
        choices=ReminderType.choices,
        default=ReminderType.INACTIVE_DEBT,
    )
    recipients = models.JSONField(default=list)

    class Meta:
        verbose_name = "Reminder log"
        verbose_name_plural = "Reminder logs"

    def __str__(self):
        return f"{self.reminder_type} @ {self.created_at.isoformat()}"
