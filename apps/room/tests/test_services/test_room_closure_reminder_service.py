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

    # ------------------------------------------------------------------
    # Creator-membership guard
    # ------------------------------------------------------------------

    def test_creator_removed_from_room_is_not_notified(self, room_with_stale_activity):
        """A creator who is no longer a room member must not receive a reminder."""
        room = room_with_stale_activity
        creator = room.created_by
        # Remove creator from the room while keeping them as created_by.
        room.users.remove(creator)

        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH) as mocked_process:
            candidates = service.run()

        assert candidates == []
        assert not mocked_process.called

    def test_creator_still_in_room_is_notified(self, room_with_stale_activity):
        """Sanity-check: creator who is still a member continues to be notified."""
        room = room_with_stale_activity
        assert room.users.filter(pk=room.created_by.pk).exists(), "pre-condition: creator must be a member"

        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH) as mocked_process:
            candidates = service.run()

        assert any(r.pk == room.pk for r in candidates)
        assert mocked_process.called

    # ------------------------------------------------------------------
    # Auto-close empty rooms
    # ------------------------------------------------------------------

    def test_empty_open_room_is_closed_on_run(self, room_with_stale_activity):
        """An open room with no members must be auto-closed during run()."""
        room = room_with_stale_activity
        room.users.clear()

        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH):
            service.run()

        room.refresh_from_db()
        assert room.status == Room.StatusChoices.CLOSED

    def test_empty_room_is_not_notified_after_autoclose(self, room_with_stale_activity):
        """Auto-closed empty rooms must not trigger any notification emails."""
        room = room_with_stale_activity
        room.users.clear()

        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH) as mocked_process:
            candidates = service.run()

        assert candidates == []
        assert not mocked_process.called

    def test_room_with_members_is_not_autoclosed(self, room_with_stale_activity):
        """Rooms that still have members must not be auto-closed."""
        room = room_with_stale_activity
        assert room.users.exists(), "pre-condition: room must have members"

        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH):
            service.run()

        room.refresh_from_db()
        assert room.status == Room.StatusChoices.OPEN

    def test_already_closed_empty_room_stays_closed(self, room_with_stale_activity):
        """Already-closed rooms must not be touched by the auto-close logic."""
        room = room_with_stale_activity
        room.users.clear()
        room.status = Room.StatusChoices.CLOSED
        room.save(update_fields=["status"])

        closed_count_before = Room.objects.filter_status_closed().count()

        service = RoomClosureReminderService(now=timezone.now())

        with mock.patch(REMINDER_SERVICE_PATH):
            service.run()

        closed_count_after = Room.objects.filter_status_closed().count()
        assert closed_count_after == closed_count_before  # no duplicate closes


# ------------------------------------------------------------------
# RoomQuerySet.without_members
# ------------------------------------------------------------------


@pytest.mark.django_db
class TestRoomQuerySetWithoutMembers:
    def test_returns_room_with_no_users(self, db):
        from apps.room.tests.factories import RoomFactory

        empty_room = RoomFactory()
        assert not empty_room.users.exists()

        qs = Room.objects.without_members()
        assert qs.filter(pk=empty_room.pk).exists()

    def test_excludes_room_with_users(self, room):
        assert room.users.exists()

        qs = Room.objects.without_members()
        assert not qs.filter(pk=room.pk).exists()

    def test_mixed_rooms_only_returns_empty_ones(self, room, db):
        from apps.room.tests.factories import RoomFactory

        empty_room = RoomFactory()

        qs = Room.objects.without_members()
        pks = list(qs.values_list("pk", flat=True))

        assert empty_room.pk in pks
        assert room.pk not in pks

