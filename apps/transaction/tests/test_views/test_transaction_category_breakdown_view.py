from decimal import Decimal

from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.models import Category


class TransactionCategoryBreakdownViewTests(BaseTestSetUp):
    def test_category_breakdown_view_sums_values_by_category(self):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")

        parent_groceries = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=self.room,
            paid_by=self.user,
            currency=self.room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        baker.make_recipe(
            "apps.transaction.tests.child_transaction",
            parent_transaction=parent_groceries,
            paid_for=self.user,
            value=Decimal("34.25"),
        )

        parent_transport = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=self.room,
            paid_by=self.user,
            currency=self.room.preferred_currency,
            category=transport,
            paid_at=timezone.now(),
        )
        baker.make_recipe(
            "apps.transaction.tests.child_transaction",
            parent_transaction=parent_transport,
            paid_for=self.user,
            value=Decimal("12.75"),
        )

        response = self.client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": self.room.slug}))
        self.assertEqual(response.status_code, 200)

        breakdowns = response.context_data["category_breakdown_by_currency"]
        self.assertEqual(len(breakdowns), 1)
        currency_breakdown = breakdowns[0]
        categories = {category["slug"]: category for category in currency_breakdown["categories"]}
        chart_data = {point["slug"]: point for point in currency_breakdown["chart_data"]}

        self.assertEqual(currency_breakdown["currency"]["id"], self.room.preferred_currency.id)
        self.assertAlmostEqual(categories["groceries"]["total_amount"], Decimal("34.25"))
        self.assertAlmostEqual(chart_data["groceries"]["value"], 34.25)
        self.assertAlmostEqual(chart_data["transport"]["value"], 12.75)

    def test_category_breakdown_view_splits_charts_per_currency(self):
        groceries = Category.objects.get(slug="groceries")
        transport = Category.objects.get(slug="transport")

        other_currency = baker.make_recipe("apps.currency.tests.currency", code="ALT")
        parent_groceries = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=self.room,
            paid_by=self.user,
            currency=self.room.preferred_currency,
            category=groceries,
            paid_at=timezone.now(),
        )
        baker.make_recipe(
            "apps.transaction.tests.child_transaction",
            parent_transaction=parent_groceries,
            paid_for=self.user,
            value=Decimal("20"),
        )

        parent_transport = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=self.room,
            paid_by=self.user,
            currency=other_currency,
            category=transport,
            paid_at=timezone.now(),
        )
        baker.make_recipe(
            "apps.transaction.tests.child_transaction",
            parent_transaction=parent_transport,
            paid_for=self.user,
            value=Decimal("5.5"),
        )

        response = self.client.get(reverse("transaction:category-breakdown", kwargs={"room_slug": self.room.slug}))
        self.assertEqual(response.status_code, 200)

        breakdowns = {
            data["currency"]["code"]: data for data in response.context_data["category_breakdown_by_currency"]
        }
        self.assertIn(self.room.preferred_currency.code, breakdowns)
        self.assertIn(other_currency.code, breakdowns)

        preferred_breakdown = breakdowns[self.room.preferred_currency.code]
        other_breakdown = breakdowns[other_currency.code]

        self.assertEqual(len(preferred_breakdown["categories"]), 1)
        self.assertEqual(len(other_breakdown["categories"]), 1)
        self.assertEqual(preferred_breakdown["categories"][0]["slug"], "groceries")
        self.assertEqual(other_breakdown["categories"][0]["slug"], "transport")
        self.assertAlmostEqual(preferred_breakdown["categories"][0]["total_amount"], Decimal("20"))
        self.assertAlmostEqual(other_breakdown["categories"][0]["total_amount"], Decimal("5.5"))

        preferred_chart = {point["slug"]: point for point in preferred_breakdown["chart_data"]}
        other_chart = {point["slug"]: point for point in other_breakdown["chart_data"]}
        self.assertAlmostEqual(preferred_chart["groceries"]["value"], 20.0)
        self.assertAlmostEqual(other_chart["transport"]["value"], 5.5)
