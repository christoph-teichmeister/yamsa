from __future__ import annotations

from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.utils import timezone

from apps.core.tests.setup import BaseTestSetUp
from apps.debt.models import ReminderLog
from apps.room.services.room_closure_reminder_service import RoomClosureReminderService
from apps.transaction.models import Category, ParentTransaction


class RoomClosureReminderServiceTestCase(BaseTestSetUp):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(
            slug=f"room-reminder-{self.room.pk}",
            name="Room reminder",
            emoji="🧹",
        )
        self._create_old_transaction()
        self.service = RoomClosureReminderService()

    def _create_old_transaction(self):
        transaction = ParentTransaction.objects.create(
            room=self.room,
            paid_by=self.user,
            currency=self.room.preferred_currency,
            description="Quiet room trigger",
            category=self.category,
        )
        timestamp = timezone.now() - timedelta(days=settings.INACTIVITY_REMINDER_DAYS + 4)
        ParentTransaction.objects.filter(pk=transaction.pk).update(lastmodified_at=timestamp)

    def test_inactive_rooms_send_room_reminder(self):
        with mock.patch(
            "apps.room.services.room_closure_reminder_service.RoomClosureReminderEmailService.process"
        ) as mocked_process:
            candidates = self.service.run()

        self.assertEqual(len(candidates), 1)
        self.assertTrue(mocked_process.called)

        log = ReminderLog.objects.get(reminder_type=self.service.REMINDER_TYPE)
        self.assertEqual(log.recipients, [self.room.created_by.email])

    def test_opted_out_creator_is_skipped(self):
        self.room.created_by.wants_to_receive_payment_reminders = False
        self.room.created_by.save(update_fields=["wants_to_receive_payment_reminders"])

        with mock.patch(
            "apps.room.services.room_closure_reminder_service.RoomClosureReminderEmailService.process"
        ) as mocked_process:
            candidates = self.service.run()

        self.assertEqual(len(candidates), 0)
        self.assertFalse(mocked_process.called)
        log = ReminderLog.objects.get(reminder_type=self.service.REMINDER_TYPE)
        self.assertEqual(log.recipients, [])

    def test_closed_rooms_are_skipped(self):
        self.room.status = self.room.StatusChoices.CLOSED
        self.room.save(update_fields=["status"])

        with mock.patch(
            "apps.room.services.room_closure_reminder_service.RoomClosureReminderEmailService.process"
        ) as mocked_process:
            candidates = self.service.run()

        self.assertEqual(len(candidates), 0)
        self.assertFalse(mocked_process.called)
        log = ReminderLog.objects.get(reminder_type=self.service.REMINDER_TYPE)
        self.assertEqual(log.recipients, [])
