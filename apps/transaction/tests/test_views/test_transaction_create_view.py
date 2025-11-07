import http
from datetime import UTC, datetime
from decimal import Decimal

from django.urls import reverse
from freezegun import freeze_time
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.views import TransactionListView


class TransactionCreateViewTestCase(BaseTestSetUp):
    @freeze_time("2020-04-04 4:20:00")
    def test_post_regular(self):
        self.assertTrue(
            self.room.users.count() > 1, "This test does not make sense, if there is only one user in the room"
        )

        client = self.reauthenticate_user(self.user)
        response = client.post(
            reverse("transaction:create", kwargs={"room_slug": self.room.slug}),
            data={
                "description": "My description",
                "currency": baker.make_recipe("apps.currency.tests.currency").id,
                "paid_at": datetime(2020, 4, 4, 4, 20, 0, tzinfo=UTC),
                "paid_by": self.user.id,
                "room": self.room.id,
                "paid_for": [str(user.id) for user in self.room.users.all()],
                "room_slug": self.room.slug,
                "value": 10,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        # Assert that we've been redirected to the transaction list view
        self.assertEqual(response.template_name[0], TransactionListView.template_name)
        self.assertIn("Room transactions", str(response.content))

        self.assertEqual(response.context_data["active_tab"], "transaction")

        self.assertTrue(
            ParentTransaction.objects.filter(description="My description", room=self.room, paid_by=self.user).exists()
        )

        child_transaction_value = Decimal(10 / self.room.users.count())
        for user in self.room.users.all():
            qs = ChildTransaction.objects.filter(paid_for=user, value=child_transaction_value)
            self.assertTrue(qs.exists(), ChildTransaction.objects.all())
