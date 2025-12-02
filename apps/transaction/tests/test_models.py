import pytest
from django.utils import timezone

from apps.currency.tests.factories import CurrencyFactory
from apps.transaction.models import Category, ParentTransaction

pytestmark = pytest.mark.django_db


class TestCategoryModel:
    def test_default_categories_seeded(self):
        expected = [
            {"slug": "accommodation", "name": "Accommodation", "color": "#6C5CE7"},
            {"slug": "groceries", "name": "Groceries", "color": "#00B894"},
            {"slug": "restaurants-and-bars", "name": "Restaurants & Bars", "color": "#FF6B6B"},
            {"slug": "transport", "name": "Transport", "color": "#0D6EFD"},
            {"slug": "activities", "name": "Activities", "color": "#FFB347"},
            {"slug": "household", "name": "Household", "color": "#6C757D"},
            {"slug": "shopping", "name": "Shopping", "color": "#D63384"},
            {"slug": "health", "name": "Health", "color": "#0DCB84"},
            {"slug": "celebrations", "name": "Celebrations", "color": "#F2C94C"},
            {"slug": "misc", "name": "Miscellaneous", "color": "#ADB5BD"},
        ]

        categories = list(Category.objects.order_by("order_index"))
        assert len(categories) == len(expected)

        for expected_category, actual in zip(expected, categories, strict=False):
            assert actual.slug == expected_category["slug"]
            assert actual.name == expected_category["name"]
            assert actual.color == expected_category["color"]
            assert actual.is_default


class TestParentTransactionModel:
    def test_parent_transaction_defaults_to_misc_category(self, user, room):
        currency = CurrencyFactory()
        transaction = ParentTransaction.objects.create(
            description="Default category check",
            paid_by=user,
            paid_at=timezone.now(),
            room=room,
            currency=currency,
        )

        assert transaction.category.slug == "misc"
