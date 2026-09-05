from decimal import Decimal

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import number_format

from apps.currency.tests.factories import CurrencyFactory
from apps.transaction.models import Category, ChildTransaction
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


def _make_child(parent_transaction, paid_for, value) -> ChildTransaction:
    return ChildTransaction.objects.create(parent_transaction=parent_transaction, paid_for=paid_for, value=value)


class TestTransactionCategoryBreakdownView:
    def test_category_breakdown_view_sums_values_by_category(self, authenticated_client, room, user):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")

        parent_groceries = ParentTransactionFactory(
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        _make_child(parent_groceries, user, Decimal("34.25"))

        parent_transport = ParentTransactionFactory(
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

    def test_category_breakdown_legend_renders_amount_once_per_category(self, authenticated_client, room, user):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")

        parent_groceries = ParentTransactionFactory(
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        _make_child(parent_groceries, user, Decimal("34.25"))

        parent_transport = ParentTransactionFactory(
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=transport,
            paid_at=timezone.now(),
        )
        _make_child(parent_transport, user, Decimal("12.75"))

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        currency_sign = room.preferred_currency.sign
        soup = BeautifulSoup(response.content.decode(), "html.parser")
        legend_list = soup.select_one(".list-group.list-group-flush")
        legend_items = legend_list.select(".list-group-item")
        assert len(legend_items) == 2

        rendered_amounts_by_slug = {}
        for item in legend_items:
            slug = item.select_one("p.text-muted.small").get_text(strip=True).lower()
            amount_span = item.select_one("span.fw-semibold")
            rendered_amounts_by_slug[slug] = amount_span.get_text(strip=True)

        expected_amounts = {
            "groceries": f"{number_format(Decimal('34.25'))}{currency_sign}",
            "transport": f"{number_format(Decimal('12.75'))}{currency_sign}",
        }
        # Regression guard: the legend previously rendered the amount twice, joined by "|"
        # (e.g. "34,25|34,25€"). Asserting the span's exact text catches that, unlike a
        # substring-count check, which the doubled string still satisfies.
        assert rendered_amounts_by_slug == expected_amounts

    def test_category_breakdown_view_splits_charts_per_currency(self, authenticated_client, room, user):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")

        other_currency = CurrencyFactory(code="ALT")
        parent_groceries = ParentTransactionFactory(
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        _make_child(parent_groceries, user, Decimal("20"))

        parent_transport = ParentTransactionFactory(
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

    def test_category_breakdown_legend_links_to_filtered_transaction_list(self, authenticated_client, room, user):
        groceries = Category.objects.get(slug="groceries")
        parent_groceries = ParentTransactionFactory(
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        _make_child(parent_groceries, user, Decimal("34.25"))

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        soup = BeautifulSoup(response.content.decode(), "html.parser")
        legend_item = soup.select_one("[data-category-legend-item]")
        assert legend_item is not None
        assert legend_item["data-category-slug"] == groceries.slug

        expected_url = (
            f"{reverse('transaction:list', kwargs={'room_slug': room.slug})}"
            f"?category={groceries.slug}&currency={room.preferred_currency.code}"
        )
        assert legend_item["hx-get"] == expected_url

    def test_category_breakdown_chart_data_carries_formatted_amount(self, authenticated_client, room, user):
        groceries = Category.objects.get(slug="groceries")
        parent_groceries = ParentTransactionFactory(
            room=room,
            paid_by=user,
            currency=room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        _make_child(parent_groceries, user, Decimal("1234.50"))

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        chart_data = response.context_data["category_breakdown_by_currency"][0]["chart_data"]
        expected_amount = (
            f"{number_format(Decimal('1234.50'), decimal_pos=2, use_l10n=True, force_grouping=True)}"
            f"{room.preferred_currency.sign}"
        )
        assert chart_data[0]["amount_label"] == expected_amount
