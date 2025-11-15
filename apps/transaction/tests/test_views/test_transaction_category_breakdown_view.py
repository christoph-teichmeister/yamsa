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

        chart_data = response.context_data["category_breakdown_chart"]
        self.assertGreaterEqual(len(chart_data), 2)
        self.assertEqual(chart_data[0]["slug"], "groceries")
        self.assertAlmostEqual(chart_data[0]["value"], 34.25)
        self.assertEqual(chart_data[1]["slug"], "transport")
        self.assertAlmostEqual(chart_data[1]["value"], 12.75)
