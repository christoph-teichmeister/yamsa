from decimal import Decimal

from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.news.models import News
from apps.transaction.tests.baker_recipes import create_parent_transaction_with_optimisation


class ParentTransactionModelTestCase(BaseTestSetUp):
    def test_news_is_generated_on_create(self):
        create_parent_transaction_with_optimisation(
            room=self.room,
            paid_by=self.user,
            paid_for_tuple=(self.user, self.guest_user),
            parent_transaction_kwargs={
                "currency": baker.make_recipe("apps.currency.tests.currency"),
                "created_by": self.user,
            },
            child_transaction_kwargs={"value": Decimal(10)},
        )

        self.assertTrue(News.objects.exists())
