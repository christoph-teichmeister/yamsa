from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.utils import timezone

from apps.core.tests.setup import BaseTestSetUp
from apps.debt.models import Debt, PaymentReminderLog
from apps.debt.services.payment_reminder_service import PaymentReminderService
from apps.transaction.models import Category, ParentTransaction


class PaymentReminderServiceTestCase(BaseTestSetUp):
    def setUp(self):
        super().setUp()
        self.category = Category.objects.create(
            slug=f"reminder-{self.room.pk}",
            name="Reminder",
            emoji="⏰",
        )
        self._create_old_transaction()
        self._create_debt()
        self.service = PaymentReminderService()

    def _create_old_transaction(self):
        transaction = ParentTransaction.objects.create(
            room=self.room,
            paid_by=self.user,
            currency=self.room.preferred_currency,
            description="Old reminder trigger",
            category=self.category,
        )
        timestamp = timezone.now() - timedelta(days=settings.PAYMENT_REMINDER_INACTIVITY_DAYS + 4)
        ParentTransaction.objects.filter(pk=transaction.pk).update(lastmodified_at=timestamp)

    def _create_debt(self):
        Debt.objects.create(
            debitor=self.user,
            creditor=self.guest_user,
            room=self.room,
            value=Decimal("42.00"),
            currency=self.room.preferred_currency,
        )

    def test_inactive_rooms_send_reminders(self):
        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = self.service.run()

        self.assertEqual(len(candidates), 1)
        self.assertTrue(mocked_process.called)
        log = PaymentReminderLog.objects.get(reminder_type=self.service.REMINDER_TYPE)
        self.assertEqual(log.recipients, [self.user.email])

    def test_opted_out_users_are_skipped(self):
        self.user.wants_to_receive_payment_reminders = False
        self.user.save(update_fields=["wants_to_receive_payment_reminders"])

        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = self.service.run()

        self.assertEqual(len(candidates), 0)
        self.assertFalse(mocked_process.called)
        log = PaymentReminderLog.objects.get(reminder_type=self.service.REMINDER_TYPE)
        self.assertEqual(log.recipients, [])

    def test_guest_users_are_skipped(self):
        Debt.objects.create(
            debitor=self.guest_user,
            creditor=self.user,
            room=self.room,
            value=Decimal("13.37"),
            currency=self.room.preferred_currency,
        )

        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = self.service.run()

        self.assertEqual(len(candidates), 1)
        self.assertTrue(mocked_process.called)
        log = PaymentReminderLog.objects.get(reminder_type=self.service.REMINDER_TYPE)
        self.assertEqual(log.recipients, [self.user.email])

    def test_closed_rooms_are_skipped(self):
        self.room.status = self.room.StatusChoices.CLOSED
        self.room.save(update_fields=["status"])

        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = self.service.run()

        self.assertEqual(len(candidates), 0)
        self.assertFalse(mocked_process.called)
        log = PaymentReminderLog.objects.get(reminder_type=self.service.REMINDER_TYPE)
        self.assertEqual(log.recipients, [])
