import pytest
from bs4 import BeautifulSoup
from django.test import Client
from freezegun import freeze_time

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.debt.models import Debt, ReminderLog
from apps.debt.tests.test_views.conftest import list_url, remind_url
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestDebtListButton:
    def _button_area(self, client: Client, room: Room, debt: Debt) -> BeautifulSoup:
        response = client.get(list_url(room))
        return BeautifulSoup(response.content.decode(), "html.parser").select_one(f'[data-debt-row="{debt.pk}"]')

    def test_the_creditor_sees_an_enabled_button(self, client: Client, room: Room, user: User, debt: Debt) -> None:
        client.force_login(user)

        row = self._button_area(client, room, debt)

        form = row.select_one(f'form[action="{remind_url(debt)}"]')
        assert form is not None
        assert form.select_one("button:not([disabled])") is not None

    def test_the_debitor_sees_no_button(self, client: Client, room: Room, debitor: User, debt: Debt) -> None:
        client.force_login(debitor)

        assert self._button_area(client, room, debt).select_one(f'form[action="{remind_url(debt)}"]') is None

    def test_after_a_reminder_the_button_is_disabled_and_names_the_next_time(
        self, client: Client, room: Room, user: User, debt: Debt
    ) -> None:
        client.force_login(user)
        with freeze_time("2026-03-14 12:00:00"):
            client.post(remind_url(debt))

        with freeze_time("2026-03-14 18:00:00"):
            row = self._button_area(client, room, debt)

        assert row.select_one("form") is None
        button = row.select_one("button[disabled]")
        hint = row.select_one(f"#{button['aria-describedby']}")
        # 12:00 UTC is 13:00 in Berlin, so the window ends at 13:00 the next day.
        assert "13:00" in hint.get_text()

    def test_the_cooldown_belongs_to_the_creditor_who_sent_it(
        self, client: Client, room: Room, user: User, debitor: User, debt: Debt
    ) -> None:
        ReminderLog.objects.create(
            reminder_type=ReminderLog.ReminderType.MANUAL_DEBT,
            room=room,
            debitor=debitor,
            created_by=UserFactory(),
        )
        client.force_login(user)

        assert self._button_area(client, room, debt).select_one("form") is not None

    def test_the_window_closes_after_a_day(self, client: Client, room: Room, user: User, debt: Debt) -> None:
        client.force_login(user)
        with freeze_time("2026-03-14 12:00:00"):
            client.post(remind_url(debt))

        with freeze_time("2026-03-15 12:01:00"):
            assert self._button_area(client, room, debt).select_one("form") is not None
