from decimal import Decimal
from unittest import mock

import pytest

from apps.debt.models import Debt, ReminderLog
from apps.debt.services.payment_reminder_service import PaymentReminderService
from apps.room.models import Room


@pytest.fixture
def debt_factory(room_with_stale_activity):
    def _factory(*, debitor, creditor, value):
        return Debt.objects.create(
            debitor=debitor,
            creditor=creditor,
            room=room_with_stale_activity,
            currency=room_with_stale_activity.preferred_currency,
            value=value,
        )

    return _factory


@pytest.fixture
def reminder_service():
    return PaymentReminderService()


@pytest.mark.django_db
class TestPaymentReminderService:
    def test_inactive_rooms_send_reminders(self, reminder_service, user, guest_user, debt_factory):
        debt_factory(debitor=user, creditor=guest_user, value=Decimal("42.00"))

        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = reminder_service.run()

        assert len(candidates) == 1
        assert mocked_process.called
        log = ReminderLog.objects.get(reminder_type=reminder_service.REMINDER_TYPE)
        assert log.recipients == [user.email]

    def test_opted_out_users_are_skipped(self, reminder_service, user, guest_user, debt_factory):
        debt_factory(debitor=user, creditor=guest_user, value=Decimal("42.00"))
        user.wants_to_receive_payment_reminders = False
        user.save(update_fields=["wants_to_receive_payment_reminders"])

        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = reminder_service.run()

        assert len(candidates) == 0
        assert not mocked_process.called
        log = ReminderLog.objects.get(reminder_type=reminder_service.REMINDER_TYPE)
        assert log.recipients == []

    def test_guest_users_are_skipped(self, reminder_service, user, guest_user, debt_factory):
        debt_factory(debitor=user, creditor=guest_user, value=Decimal("42.00"))
        debt_factory(debitor=guest_user, creditor=user, value=Decimal("13.37"))

        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = reminder_service.run()

        assert len(candidates) == 1
        assert mocked_process.called
        log = ReminderLog.objects.get(reminder_type=reminder_service.REMINDER_TYPE)
        assert log.recipients == [user.email]

    def test_closed_rooms_are_skipped(self, reminder_service, user, guest_user, debt_factory, room_with_stale_activity):
        debt_factory(debitor=user, creditor=guest_user, value=Decimal("42.00"))
        room_with_stale_activity.status = Room.StatusChoices.CLOSED
        room_with_stale_activity.save(update_fields=["status"])

        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderEmailService.process"
        ) as mocked_process:
            candidates = reminder_service.run()

        assert len(candidates) == 0
        assert not mocked_process.called
        log = ReminderLog.objects.get(reminder_type=reminder_service.REMINDER_TYPE)
        assert log.recipients == []
