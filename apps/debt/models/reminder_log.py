from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext_lazy as _


class ReminderLog(CommonInfo):
    class ReminderType(models.TextChoices):
        """TextChoices keeps the recorded reminder type human-readable in historical logs."""

        INACTIVE_DEBT = "inactive_debt", _("Inactive debt reminder")
        INACTIVE_ROOM = "inactive_room", _("Inactive room reminder")

    reminder_type = models.CharField(
        max_length=50,
        choices=ReminderType.choices,
        default=ReminderType.INACTIVE_DEBT,
    )
    recipients = models.JSONField(default=list)

    class Meta:
        verbose_name = _("Reminder log")
        verbose_name_plural = _("Reminder logs")

    def __str__(self):
        return f"{self.reminder_type} @ {self.created_at.isoformat()}"
