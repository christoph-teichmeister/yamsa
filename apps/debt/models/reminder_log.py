import zlib
from datetime import datetime, timedelta

from ambient_toolbox.models import CommonInfo
from django.db import connection, models, transaction
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

    @classmethod
    def claim_window(cls, reminder_type: str, *, interval: timedelta, now: datetime) -> "ReminderLog | None":
        """Record a new wave and return its log, or None if one ran within `interval`.

        The log is written before any mail goes out: a mail failure or a concurrent request then
        sees the window as taken instead of resending. Postgres serialises the check-and-insert
        with an advisory lock (there is no row to lock before the first wave); SQLite, used only
        in tests, has a single writer anyway.
        """
        with transaction.atomic():
            if connection.vendor == "postgresql":
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [zlib.crc32(reminder_type.encode())])
            last_log = cls.objects.filter(reminder_type=reminder_type).order_by("-created_at").first()
            if last_log and last_log.created_at + interval > now:
                return None
            return cls.objects.create(reminder_type=reminder_type)

    def __str__(self) -> str:
        return f"{self.reminder_type} @ {self.created_at.isoformat()}"
