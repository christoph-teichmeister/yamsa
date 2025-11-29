from unittest import mock

import pytest
from django.utils import timezone

from apps.debt.models import ReminderLog
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

        log = ReminderLog.objects.get(reminder_type=service.REMINDER_TYPE)
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

        log = ReminderLog.objects.get(reminder_type=service.REMINDER_TYPE)
        assert log.recipients == []
