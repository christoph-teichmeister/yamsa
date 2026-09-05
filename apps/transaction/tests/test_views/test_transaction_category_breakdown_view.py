from decimal import Decimal

import pytest
from bs4 import BeautifulSoup
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import number_format

from apps.currency.tests.factories import CurrencyFactory
from apps.transaction.constants import CHART_SMALL_SLICE_BUCKET_COLOR
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
        # An anchor with a real href, so Enter activates it natively and it survives without JS.
        assert legend_item.name == "a"
        assert legend_item["href"] == expected_url

    def test_category_breakdown_legend_entry_needs_no_scripted_keyboard_trigger(self, authenticated_client, room, user):
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

        # Regression guard: the entry used to be a div with hx-trigger="click keyup[...]" — htmx splits
        # that attribute on commas only, so the keyup half was dropped and the row was unreachable by
        # keyboard. Both attributes also compile via new Function(), which the project's CSP forbids.
        assert "hx-trigger" not in legend_item.attrs
        assert not any(attribute.startswith("hx-on") for attribute in legend_item.attrs)
        # No aria-label either: it would override the row's content as the accessible name and hide
        # the amount from assistive tech.
        assert "aria-label" not in legend_item.attrs
        assert legend_item.select_one("span.fw-semibold").get_text(strip=True)

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

    def test_category_breakdown_collapses_small_slices_into_one_bucket(self, authenticated_client, room, user):
        big_category = Category.objects.get(slug="restaurants-and-bars")
        first_small_category = Category.objects.get(slug="groceries")
        second_small_category = Category.objects.get(slug="transport")

        amounts_by_category = {
            big_category: Decimal("1000.00"),
            first_small_category: Decimal("10.00"),
            second_small_category: Decimal("5.00"),
        }
        for category, amount in amounts_by_category.items():
            parent_transaction = ParentTransactionFactory(
                room=room,
                paid_by=user,
                currency=room.preferred_currency,
                category=category,
                paid_at=timezone.now(),
            )
            _make_child(parent_transaction, user, amount)

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        breakdown = response.context_data["category_breakdown_by_currency"][0]
        chart_data = breakdown["chart_data"]

        assert [point["slug"] for point in chart_data] == [big_category.slug, None]
        bucket_point = chart_data[-1]
        assert bucket_point["value"] == 15.0
        assert "2" in bucket_point["label"]

        # The legend stays complete, so every category remains reachable for filtering.
        assert {category["slug"] for category in breakdown["categories"]} == {
            category.slug for category in amounts_by_category
        }

    def test_category_breakdown_keeps_a_lone_small_slice_as_its_own_category(self, authenticated_client, room, user):
        big_category = Category.objects.get(slug="restaurants-and-bars")
        small_category = Category.objects.get(slug="groceries")

        for category, amount in ((big_category, Decimal("1000.00")), (small_category, Decimal("5.00"))):
            parent_transaction = ParentTransactionFactory(
                room=room,
                paid_by=user,
                currency=room.preferred_currency,
                category=category,
                paid_at=timezone.now(),
            )
            _make_child(parent_transaction, user, amount)

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        chart_data = response.context_data["category_breakdown_by_currency"][0]["chart_data"]
        assert [point["slug"] for point in chart_data] == [big_category.slug, small_category.slug]

    def test_category_breakdown_measures_small_slices_per_currency(self, authenticated_client, room, user):
        other_currency = CurrencyFactory(code="ALT")
        big_category = Category.objects.get(slug="restaurants-and-bars")
        first_small_category = Category.objects.get(slug="groceries")
        second_small_category = Category.objects.get(slug="transport")

        for category, amount in (
            (big_category, Decimal("1000.00")),
            (first_small_category, Decimal("10.00")),
            (second_small_category, Decimal("5.00")),
        ):
            parent_transaction = ParentTransactionFactory(
                room=room,
                paid_by=user,
                currency=room.preferred_currency,
                category=category,
                paid_at=timezone.now(),
            )
            _make_child(parent_transaction, user, amount)

        # The same absolute amounts carry the whole second currency, so nothing is collapsed there.
        for category, amount in ((first_small_category, Decimal("10.00")), (second_small_category, Decimal("5.00"))):
            parent_transaction = ParentTransactionFactory(
                room=room,
                paid_by=user,
                currency=other_currency,
                category=category,
                paid_at=timezone.now(),
            )
            _make_child(parent_transaction, user, amount)

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        assert response.status_code == 200

        breakdowns = {
            data["currency"]["code"]: data for data in response.context_data["category_breakdown_by_currency"]
        }
        preferred_slugs = [point["slug"] for point in breakdowns[room.preferred_currency.code]["chart_data"]]
        other_slugs = [point["slug"] for point in breakdowns[other_currency.code]["chart_data"]]

        assert preferred_slugs == [big_category.slug, None]
        assert other_slugs == [first_small_category.slug, second_small_category.slug]

    def test_category_breakdown_never_buckets_a_category_that_is_tappable_on_its_own(
        self, authenticated_client, room, user
    ):
        # The three slivers add up to 0.7%, so the bucket stays under the threshold. It must not
        # grow by swallowing the 22% category next to it - that would hide real spend.
        amounts_by_slug = {
            "restaurants-and-bars": Decimal("1000.00"),
            "transport": Decimal("300.00"),
            "groceries": Decimal("3.00"),
            "household": Decimal("3.00"),
            "shopping": Decimal("3.00"),
        }
        for slug, amount in amounts_by_slug.items():
            parent_transaction = ParentTransactionFactory(
                room=room,
                paid_by=user,
                currency=room.preferred_currency,
                category=Category.objects.get(slug=slug),
                paid_at=timezone.now(),
            )
            _make_child(parent_transaction, user, amount)

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        chart_data = response.context_data["category_breakdown_by_currency"][0]["chart_data"]

        assert [point["slug"] for point in chart_data] == ["restaurants-and-bars", "transport", None]
        bucket_point = chart_data[-1]
        assert bucket_point["value"] == 9.0
        assert "3" in bucket_point["label"]
        assert bucket_point["color"] == CHART_SMALL_SLICE_BUCKET_COLOR

    def test_category_breakdown_never_collapses_every_category_into_the_bucket(self, authenticated_client, room, user):
        # Six equal categories are each below the threshold; collapsing all of them would leave a
        # donut of one full ring that shows nothing.
        slugs = ("restaurants-and-bars", "transport", "groceries", "household", "shopping", "health")
        for slug in slugs:
            parent_transaction = ParentTransactionFactory(
                room=room,
                paid_by=user,
                currency=room.preferred_currency,
                category=Category.objects.get(slug=slug),
                paid_at=timezone.now(),
            )
            _make_child(parent_transaction, user, Decimal("10.00"))

        response = authenticated_client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": room.slug}))
        chart_data = response.context_data["category_breakdown_by_currency"][0]["chart_data"]

        assert len(chart_data) == len(slugs)
        assert all(point["slug"] is not None for point in chart_data)

    def test_category_breakdown_bucket_color_is_not_a_seeded_category_color(self, authenticated_client, room, user):
        seeded_colors = {(category.color or "").lower() for category in Category.objects.exclude(color="")}
        # Two adjacent slices in the exact same grey are indistinguishable.
        assert CHART_SMALL_SLICE_BUCKET_COLOR.lower() not in seeded_colors
