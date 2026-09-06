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


class TestOpenRoomOrdering:
    def test_rooms_the_user_owes_in_come_before_rooms_owing_the_user(
        self, authenticated_client, room, user, guest_user
    ):
        currency = CurrencyFactory(sign="€")
        receiving_room = RoomFactory(created_by=user)
        receiving_room.users.add(user, guest_user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="5.00")
        create_debt(room=receiving_room, debitor=guest_user, creditor=user, currency=currency, value="80.00")

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert [entry.slug for entry in entries] == [room.slug, receiving_room.slug]

    def test_within_the_same_direction_the_larger_amount_comes_first(
        self, authenticated_client, room, user, guest_user
    ):
        currency = CurrencyFactory(sign="€")
        bigger_room = RoomFactory(created_by=user)
        bigger_room.users.add(user, guest_user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="5.00")
        create_debt(room=bigger_room, debitor=user, creditor=guest_user, currency=currency, value="500.00")

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert [entry.slug for entry in entries] == [bigger_room.slug, room.slug]

    def test_settled_rooms_come_last(self, authenticated_client, room, user, guest_user):
        owing_room = RoomFactory(created_by=user)
        owing_room.users.add(user, guest_user)
        create_debt(room=owing_room, debitor=user, creditor=guest_user, currency=CurrencyFactory(), value="1.00")

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert [entry.slug for entry in entries] == [owing_room.slug, room.slug]

    def test_a_room_owing_in_one_currency_and_receiving_in_another_ranks_as_owing(
        self, authenticated_client, room, user, guest_user
    ):
        mixed_room = RoomFactory(created_by=user)
        mixed_room.users.add(user, guest_user)
        create_debt(
            room=mixed_room, debitor=user, creditor=guest_user, currency=CurrencyFactory(sign="€"), value="1.00"
        )
        create_debt(
            room=mixed_room, debitor=guest_user, creditor=user, currency=CurrencyFactory(sign="$"), value="99.00"
        )

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert entries[0].slug == mixed_room.slug
        assert entries[0].user_owes is True


class TestOpenBalanceSummary:
    def test_closed_rooms_are_left_out_of_the_totals(self, authenticated_client, room, closed_room, user, guest_user):
        currency = CurrencyFactory(sign="€")
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=closed_room, debitor=user, creditor=guest_user, currency=currency, value="90.00")

        totals = authenticated_client.get(reverse("core:welcome")).context_data["open_balance_totals"]

        assert [total.owed_by_user for total in totals] == [Decimal("10.00")]

    def test_the_summed_amount_is_rendered(self, authenticated_client, room, user, guest_user):
        currency = CurrencyFactory(sign="€")
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user, guest_user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=currency, value="10.00")
        create_debt(room=other_room, debitor=user, creditor=guest_user, currency=currency, value="2.50")

        content = authenticated_client.get(reverse("core:welcome")).content.decode()

        assert "12.50€" in content or "12,50€" in content

    def test_a_user_without_debts_gets_no_summary(self, authenticated_client, room):
        response = authenticated_client.get(reverse("core:welcome"))

        assert response.context_data["open_balance_totals"] == []
        assert "room-balance-summary" not in response.content.decode()
