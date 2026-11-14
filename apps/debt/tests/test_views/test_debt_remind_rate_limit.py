from unittest import mock

import pytest
from django.core import mail
from django.test import Client
from freezegun import freeze_time

from apps.account.models import User
from apps.debt.models import Debt, ReminderLog
from apps.debt.tests.test_views.conftest import PUSH, remind_url
from apps.room.models import Room
from apps.transaction.tests.conftest import create_parent_transaction_with_optimisation

pytestmark = pytest.mark.django_db


class TestRateLimit:
    def test_a_second_reminder_within_a_day_sends_nothing(self, client: Client, user: User, debt: Debt) -> None:
        client.force_login(user)
        with freeze_time("2026-03-14 12:00:00"):
            client.post(remind_url(debt))
            mail.outbox.clear()

        with freeze_time("2026-03-15 11:59:00"), mock.patch(PUSH) as push:
            client.post(remind_url(debt))

        push.assert_not_called()
        assert mail.outbox == []
        assert ReminderLog.objects.filter(reminder_type=ReminderLog.ReminderType.MANUAL_DEBT).count() == 1

    def test_a_reminder_is_possible_again_after_a_day(self, client: Client, user: User, debt: Debt) -> None:
        client.force_login(user)
        with freeze_time("2026-03-14 12:00:00"):
            client.post(remind_url(debt))

        with freeze_time("2026-03-15 12:00:01"), mock.patch(PUSH) as push:
            client.post(remind_url(debt))

        push.assert_called_once()
        assert ReminderLog.objects.filter(reminder_type=ReminderLog.ReminderType.MANUAL_DEBT).count() == 2

    def test_the_limit_survives_the_optimiser_recreating_the_debt(
        self, client: Client, room: Room, user: User, debitor: User, debt: Debt
    ) -> None:
        client.force_login(user)
        client.post(remind_url(debt))
        create_parent_transaction_with_optimisation(
            room=room,
            paid_by=user,
            paid_for_tuple=(debitor,),
            parent_transaction_kwargs={"currency": debt.currency},
        )
        recreated = Debt.objects.get(room=room, settled=False)
        assert recreated.pk != debt.pk

        with mock.patch(PUSH) as push:
            client.post(remind_url(recreated))

        push.assert_not_called()
