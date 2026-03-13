import pytest
from django.utils import timezone

from apps.currency.tests.factories import CurrencyFactory
from apps.transaction.models import ParentTransaction

pytestmark = pytest.mark.django_db


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
