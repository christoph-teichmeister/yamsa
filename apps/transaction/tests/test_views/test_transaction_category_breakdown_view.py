from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from apps.transaction.models import Category

pytestmark = pytest.mark.django_db


def _make_child(parent_transaction, paid_for, value):
    baker.make_recipe(
        "apps.transaction.tests.child_transaction",
        parent_transaction=parent_transaction,
        paid_for=paid_for,
        value=value,
    )


class TestTransactionCategoryBreakdownView:
    def test_category_breakdown_view_sums_values_by_category(self, authenticated_client, room, user):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")

        parent_groceries = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        _make_child(parent_groceries, user, Decimal("34.25"))

        parent_transport = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=transport,
            paid_at=timezone.now(),
        )
        _make_child(parent_transport, user, Decimal("12.75"))

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        breakdowns = response.context_data["category_breakdown_by_currency"]
        assert len(breakdowns) == 1
        currency_breakdown = breakdowns[0]
        categories = {category["slug"]: category for category in currency_breakdown["categories"]}
        chart_data = {point["slug"]: point for point in currency_breakdown["chart_data"]}

        assert currency_breakdown["currency"]["id"] == room.preferred_currency.id
        assert categories["groceries"]["total_amount"] == Decimal("34.25")
        assert chart_data["groceries"]["value"] == 34.25
        assert chart_data["transport"]["value"] == 12.75

    def test_category_breakdown_view_splits_charts_per_currency(self, authenticated_client, room, user):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")

        other_currency = baker.make_recipe("apps.currency.tests.currency", code="ALT")
        parent_groceries = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        _make_child(parent_groceries, user, Decimal("20"))

        parent_transport = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=room,
            paid_by=user,
            currency=other_currency,
            category=transport,
            paid_at=timezone.now(),
        )
        _make_child(parent_transport, user, Decimal("5.5"))

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        breakdowns = {
            data["currency"]["code"]: data for data in response.context_data["category_breakdown_by_currency"]
        }
        assert room.preferred_currency.code in breakdowns
        assert other_currency.code in breakdowns

        preferred_breakdown = breakdowns[room.preferred_currency.code]
        other_breakdown = breakdowns[other_currency.code]

        assert len(preferred_breakdown["categories"]) == 1
        assert len(other_breakdown["categories"]) == 1
        assert preferred_breakdown["categories"][0]["slug"] == "groceries"
        assert other_breakdown["categories"][0]["slug"] == "transport"
        assert preferred_breakdown["categories"][0]["total_amount"] == Decimal("20")
        assert other_breakdown["categories"][0]["total_amount"] == Decimal("5.5")

        preferred_chart = {point["slug"]: point for point in preferred_breakdown["chart_data"]}
        other_chart = {point["slug"]: point for point in other_breakdown["chart_data"]}
        assert preferred_chart["groceries"]["value"] == 20.0
        assert other_chart["transport"]["value"] == 5.5
