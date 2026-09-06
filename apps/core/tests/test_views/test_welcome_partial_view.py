import http
from decimal import Decimal
from unittest import mock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.tests.factories import RoomFactory

pytestmark = pytest.mark.django_db


def create_debt(*, room, debitor, creditor, currency, value):
    return Debt.objects.create(
        room=room,
        debitor=debitor,
        creditor=creditor,
        currency=currency,
        value=Decimal(value),
    )


def add_rooms_with_debts(*, user, guest_user, currency, count):
    for _ in range(count):
        extra_room = RoomFactory(created_by=user)
        extra_room.users.add(user, guest_user)
        create_debt(room=extra_room, debitor=user, creditor=guest_user, currency=currency, value="3.00")


class TestWelcomePartialView:
    def test_anonymous_user_is_redirected_to_the_login(self, client):
        response = client.get(reverse("core:welcome"))

        assert response.status_code == http.HTTPStatus.FOUND
        assert response.url == reverse("account:login")

    def test_rooms_are_grouped_by_status(self, authenticated_client, room, closed_room):
        response = authenticated_client.get(reverse("core:welcome"))

        assert response.status_code == http.HTTPStatus.OK
        context = response.context_data
        assert [entry.slug for entry in context["open_room_entries"]] == [room.slug]
        assert [entry.slug for entry in context["closed_room_entries"]] == [closed_room.slug]
        assert context["other_room_entries"] == []
        assert context["has_room_entries"] is True

    def test_room_name_and_balance_are_rendered(self, authenticated_client, room, user, guest_user):
        currency = CurrencyFactory(sign="€")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="12.50")

        content = authenticated_client.get(reverse("core:welcome")).content.decode()

        assert room.name in content
        assert "12.50€" in content or "12,50€" in content

    def test_a_settled_room_shows_the_all_settled_hint(self, authenticated_client, room):
        content = authenticated_client.get(reverse("core:welcome")).content.decode()

        assert "All settled" in content

    def test_the_news_feed_is_gone_from_the_context(self, authenticated_client, room):
        context = authenticated_client.get(reverse("core:welcome")).context_data

        assert "news" not in context
        assert "highlighted_news" not in context

    def test_query_count_does_not_grow_with_the_number_of_rooms(self, authenticated_client, user, guest_user):
        currency = CurrencyFactory()
        add_rooms_with_debts(user=user, guest_user=guest_user, currency=currency, count=2)
        with CaptureQueriesContext(connection) as few_rooms:
            authenticated_client.get(reverse("core:welcome"))

        add_rooms_with_debts(user=user, guest_user=guest_user, currency=currency, count=3)
        with CaptureQueriesContext(connection) as more_rooms:
            authenticated_client.get(reverse("core:welcome"))

        assert len(more_rooms) == len(few_rooms)

    def test_rendering_the_dashboard_does_not_trigger_reminder_mails(self, authenticated_client, room):
        with mock.patch(
            "apps.debt.services.payment_reminder_service.PaymentReminderService.run_if_due"
        ) as payment_reminder:
            authenticated_client.get(reverse("core:welcome"))

        payment_reminder.assert_not_called()
