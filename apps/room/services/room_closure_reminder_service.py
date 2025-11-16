from __future__ import annotations

from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from apps.debt.models import ReminderLog
from apps.mail.services.room_closure_reminder_mail_service import RoomClosureReminderEmailService
from apps.room.models import Room


class RoomClosureReminderService:
    """Notify room creators when their open rooms have been quiet for too long."""

    REMINDER_TYPE = ReminderLog.ReminderType.INACTIVE_ROOM
    HEARTBEAT_INTERVAL = timedelta(days=30)  # Keep room nudges to roughly one-per-month bursts.

    def __init__(self, *, now: datetime | None = None):
        self.now = now or timezone.now()
        # Any room with activity older than this threshold becomes a closure candidate.
        self.threshold = self.now - timedelta(days=settings.INACTIVITY_REMINDER_DAYS)

    def run(self) -> list[Room]:
        """Tell room owners to revisit rooms that have stayed open without activity."""
        if not settings.INACTIVITY_REMINDER_ENABLED:
            return []

        rooms = self._collect_rooms()
        recipients: list[str] = []
        candidates: list[Room] = []
        for room in rooms:
            creator = room.created_by
            if not self._should_notify_creator(creator):
                continue

            RoomClosureReminderEmailService(
                recipient=creator,
                room_name=room.name,
                inactivity_days=settings.INACTIVITY_REMINDER_DAYS,
                room_link=self._build_room_link(room),
            ).process()

            recipients.append(creator.email)
            candidates.append(room)

        ReminderLog.objects.create(
            reminder_type=self.REMINDER_TYPE,
            recipients=sorted(set(recipients)),
        )

        return candidates

    def run_if_due(self) -> list[Room]:
        """Guard the execution behind the heartbeat to avoid spamming creators."""
        if not self.should_run():
            return []
        return self.run()

    def should_run(self) -> bool:
        """Check whether enough time has passed since the last reminder wave."""
        if not settings.INACTIVITY_REMINDER_ENABLED:
            return False

        last_log = ReminderLog.objects.filter(reminder_type=self.REMINDER_TYPE).order_by("-created_at").first()

        if not last_log:
            return True

        return last_log.created_at + self.HEARTBEAT_INTERVAL <= self.now

    def _collect_rooms(self):
        """Find open rooms that have been idle past the inactivity threshold."""
        return (
            Room.objects.annotate_last_transaction_lastmodified_at_date()
            .filter(status=Room.StatusChoices.OPEN)
            .filter(
                Q(last_transaction_created_at_date__lt=self.threshold)
                | Q(last_transaction_created_at_date__isnull=True)
            )
            .filter(created_by__isnull=False)
            .select_related("created_by")
        )

    @staticmethod
    def _should_notify_creator(creator):
        """Skip guests or creators who opted out of room-related reminders."""
        if not creator:
            return False
        if creator.is_guest:
            return False
        return creator.wants_to_receive_room_reminders

    @staticmethod
    def _build_room_link(room: Room) -> str:
        """Point creators back to the room detail to confirm closure if needed."""
        backend = settings.BACKEND_URL.rstrip("/")
        return f"{backend}{reverse('room:detail', kwargs={'room_slug': room.slug})}"
