from decimal import Decimal
from io import StringIO
from unittest import mock

import pytest
from django.core.management import call_command

from apps.account.models import User
from apps.debt.models import Debt, ReminderLog
from apps.room.models import Room

PAYMENT_MAIL = "apps.mail.services.payment_reminder_mail_service.PaymentReminderEmailService.process"
CLOSURE_RUN = "apps.room.services.room_closure_reminder_service.RoomClosureReminderService.run"


def _run_command() -> str:
    out = StringIO()
    call_command("send_payment_reminders", stdout=out)
    return out.getvalue()


@pytest.fixture
def stale_debt(room_with_stale_activity: Room, user: User, guest_user: User) -> Debt:
    return Debt.objects.create(
        debitor=user,
        creditor=guest_user,
        room=room_with_stale_activity,
        currency=room_with_stale_activity.preferred_currency,
        value=Decimal("42.00"),
    )


@pytest.mark.django_db
class TestSendPaymentRemindersCommand:
    def test_mails_the_debitor_and_logs_the_wave(self, stale_debt: Debt) -> None:
        with mock.patch(PAYMENT_MAIL) as mocked_process, mock.patch(CLOSURE_RUN, return_value=[]):
            output = _run_command()

        assert mocked_process.call_count == 1
        assert "Sent 1 payment reminders" in output
        log = ReminderLog.objects.get(reminder_type=ReminderLog.ReminderType.INACTIVE_DEBT)
        assert log.recipients == [stale_debt.debitor.email]

    def test_opted_out_debitor_gets_no_mail(self, stale_debt: Debt) -> None:
        stale_debt.debitor.wants_to_receive_payment_reminders = False
        stale_debt.debitor.save(update_fields=["wants_to_receive_payment_reminders"])

        with mock.patch(PAYMENT_MAIL) as mocked_process, mock.patch(CLOSURE_RUN, return_value=[]):
            output = _run_command()

        assert not mocked_process.called
        assert "Sent 0 payment reminders" in output

    def test_settled_debt_is_not_a_candidate(self, stale_debt: Debt) -> None:
        stale_debt.settled = True
        stale_debt.save(update_fields=["settled"])

        with mock.patch(PAYMENT_MAIL) as mocked_process, mock.patch(CLOSURE_RUN, return_value=[]):
            _run_command()

        assert not mocked_process.called

    def test_command_does_not_consult_the_heartbeat_window(self, stale_debt: Debt) -> None:
        """The command calls run(), not run_if_due(): a second invocation mails again."""
        with mock.patch(PAYMENT_MAIL) as mocked_process, mock.patch(CLOSURE_RUN, return_value=[]):
            _run_command()
            _run_command()

        assert mocked_process.call_count == 2
