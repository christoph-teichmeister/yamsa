from datetime import timedelta
from unittest import mock

import pytest
from django.test import override_settings
from django.utils import timezone

from apps.debt.models import ReminderLog
from apps.room.models import Room
from apps.room.services.room_closure_reminder_service import RoomClosureReminderService

REMINDER_SERVICE_PATH = "apps.room.services.room_closure_reminder_service.RoomClosureReminderEmailService.process"


@pytest.mark.django_db
class TestRoomClosureReminderService:
    def test_notifies_creator(self, room_with_stale_activity):
        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH) as mocked_process:
            candidates = service.run()

        assert candidates
        assert candidates[0].pk == room_with_stale_activity.pk
        assert mocked_process.called

        log = ReminderLog.objects.filter(reminder_type=service.REMINDER_TYPE).latest("created_at")
        assert log.recipients == [room_with_stale_activity.created_by.email]

    def test_respects_creator_opt_out(self, room_with_stale_activity):
        room = room_with_stale_activity
        room.created_by.wants_to_receive_room_reminders = False
        room.created_by.save(update_fields=["wants_to_receive_room_reminders"])
        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH) as mocked_process:
            candidates = service.run()

        assert candidates == []
        assert not mocked_process.called

        log = ReminderLog.objects.filter(reminder_type=service.REMINDER_TYPE).latest("created_at")
        assert log.recipients == []

    def test_closed_rooms_are_skipped(self, room_with_stale_activity):
        room = room_with_stale_activity
        room.status = Room.StatusChoices.CLOSED
        room.save(update_fields=["status"])
        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH) as mocked_process:
            candidates = service.run()

        assert candidates == []
        assert not mocked_process.called

        log = ReminderLog.objects.filter(reminder_type=service.REMINDER_TYPE).latest("created_at")
        assert log.recipients == []

    @override_settings(INACTIVITY_REMINDER_ENABLED=False)
    def test_should_run_returns_false_when_disabled(self):
        service = RoomClosureReminderService(now=timezone.now())

        assert not service.should_run()

    def test_should_run_respects_heartbeat_interval(self):
        ReminderLog.objects.create(reminder_type=RoomClosureReminderService.REMINDER_TYPE, recipients=[])
        last_log = ReminderLog.objects.order_by("-created_at").first()
        service = RoomClosureReminderService(
            now=last_log.created_at + RoomClosureReminderService.HEARTBEAT_INTERVAL - timedelta(seconds=1)
        )

        assert not service.should_run()

    def test_should_run_after_heartbeat_expires(self):
        ReminderLog.objects.create(reminder_type=RoomClosureReminderService.REMINDER_TYPE, recipients=[])
        last_log = ReminderLog.objects.order_by("-created_at").first()
        service = RoomClosureReminderService(
            now=last_log.created_at + RoomClosureReminderService.HEARTBEAT_INTERVAL + timedelta(seconds=1)
        )

        assert service.should_run()

    def test_run_if_due_skips_when_not_ready(self):
        service = RoomClosureReminderService(now=timezone.now())

        with (
            mock.patch.object(service, "should_run", return_value=False),
            mock.patch.object(service, "run") as mocked_run,
        ):
            assert service.run_if_due() == []
            mocked_run.assert_not_called()
