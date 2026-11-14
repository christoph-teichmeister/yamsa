import http
from unittest import mock

import pytest
from django.core import mail
from django.test import Client

from apps.account.models import User
from apps.debt.models import Debt, ReminderLog
from apps.debt.tests.test_views.conftest import PUSH, list_url, remind_url

pytestmark = pytest.mark.django_db


class TestSendingAReminder:
    def test_the_creditor_reminds_the_debitor_by_push_and_mail(
        self, client: Client, user: User, debitor: User, debt: Debt
    ) -> None:
        client.force_login(user)

        with mock.patch(PUSH) as push:
            response = client.post(remind_url(debt))

        assert response.status_code == http.HTTPStatus.FOUND
        assert response.url == list_url(debt.room)
        push.assert_called_once_with(debitor)
        assert [message.to for message in mail.outbox] == [[debitor.email]]
        assert user.name in mail.outbox[0].subject
        assert user.name in mail.outbox[0].body
        assert str(debt.value) in mail.outbox[0].body

    def test_the_attempt_is_logged_as_a_manual_reminder(
        self, client: Client, user: User, debitor: User, debt: Debt
    ) -> None:
        client.force_login(user)

        client.post(remind_url(debt))

        log = ReminderLog.objects.get(reminder_type=ReminderLog.ReminderType.MANUAL_DEBT)
        assert (log.created_by, log.debitor, log.room, log.recipients) == (user, debitor, debt.room, [debitor.email])

    def test_a_debitor_who_opted_out_of_payment_mails_gets_no_mail(
        self, client: Client, user: User, debitor: User, debt: Debt
    ) -> None:
        debitor.wants_to_receive_payment_reminders = False
        debitor.save(update_fields=["wants_to_receive_payment_reminders"])
        client.force_login(user)

        with mock.patch(PUSH) as push:
            client.post(remind_url(debt))

        push.assert_called_once()
        assert mail.outbox == []
