import http
from datetime import datetime, timedelta
from decimal import Decimal
from unittest import mock

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.currency.tests.factories import CurrencyFactory
from apps.debt.models import Debt
from apps.room.models import Room
from apps.room.tests.factories import RoomFactory
from apps.transaction.models import ParentTransaction
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


def create_debt(*, room, debitor, creditor, currency, value):
    return Debt.objects.create(
        room=room,
        debitor=debitor,
        creditor=creditor,
        currency=currency,
        value=Decimal(value),
    )


def add_transaction(*, room, user, at: datetime):
    """Give the room a transaction whose lastmodified_at is exactly ``at``.

    CommonInfo stamps lastmodified_at on every save, so the timestamp has to be forced past
    the ORM with an update() - assigning it before save() would simply be overwritten.
    """
    transaction = ParentTransactionFactory(room=room, paid_by=user, currency=room.preferred_currency)
    ParentTransaction.objects.filter(pk=transaction.pk).update(lastmodified_at=at)
    return transaction


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

    def test_open_rooms_are_ordered_by_their_latest_transaction(self, authenticated_client, room, user, guest_user):
        now = timezone.now()
        stale_room = RoomFactory(created_by=user)
        stale_room.users.add(user, guest_user)
        freshest_room = RoomFactory(created_by=user)
        freshest_room.users.add(user, guest_user)
        add_transaction(room=stale_room, user=user, at=now - timedelta(days=30))
        add_transaction(room=room, user=user, at=now - timedelta(days=2))
        add_transaction(room=freshest_room, user=user, at=now - timedelta(minutes=5))

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert [entry.slug for entry in entries] == [freshest_room.slug, room.slug, stale_room.slug]

    def test_only_the_latest_transaction_of_a_room_counts(self, authenticated_client, room, user, guest_user):
        now = timezone.now()
        other_room = RoomFactory(created_by=user)
        other_room.users.add(user, guest_user)
        add_transaction(room=room, user=user, at=now - timedelta(days=90))
        add_transaction(room=room, user=user, at=now - timedelta(minutes=1))
        add_transaction(room=other_room, user=user, at=now - timedelta(days=1))

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert [entry.slug for entry in entries] == [room.slug, other_room.slug]

    def test_the_open_balance_no_longer_decides_the_order(self, authenticated_client, room, user, guest_user):
        now = timezone.now()
        settled_room = RoomFactory(created_by=user)
        settled_room.users.add(user, guest_user)
        create_debt(room=room, debitor=user, creditor=guest_user, currency=CurrencyFactory(), value="500.00")
        add_transaction(room=room, user=user, at=now - timedelta(days=10))
        add_transaction(room=settled_room, user=user, at=now - timedelta(hours=1))

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert [entry.slug for entry in entries] == [settled_room.slug, room.slug]

    def test_a_room_without_transactions_is_ranked_by_its_own_timestamp(
        self, authenticated_client, room, user, guest_user
    ):
        # A room created just now has nothing to show yet and must not start out at the bottom.
        add_transaction(room=room, user=user, at=timezone.now() - timedelta(days=3))
        brand_new_room = RoomFactory(created_by=user)
        brand_new_room.users.add(user, guest_user)

        entries = authenticated_client.get(reverse("core:welcome")).context_data["open_room_entries"]

        assert [entry.slug for entry in entries] == [brand_new_room.slug, room.slug]

    def test_closed_rooms_are_ordered_by_their_latest_transaction_too(
        self, authenticated_client, closed_room, user, guest_user
    ):
        now = timezone.now()
        other_closed_room = RoomFactory(created_by=user, status=Room.StatusChoices.CLOSED)
        other_closed_room.users.add(user, guest_user)
        add_transaction(room=closed_room, user=user, at=now - timedelta(days=5))
        add_transaction(room=other_closed_room, user=user, at=now - timedelta(days=1))

        entries = authenticated_client.get(reverse("core:welcome")).context_data["closed_room_entries"]

        assert [entry.slug for entry in entries] == [other_closed_room.slug, closed_room.slug]

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
