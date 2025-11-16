import http
from decimal import Decimal

from django.urls import reverse
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.utils import split_total_across_paid_for


class TransactionEditViewTests(BaseTestSetUp):
    def test_post_rebalances_child_transactions_when_total_changes(self):
        parent_transaction = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=self.room,
            paid_by=self.user,
        )
        baker.make_recipe(
            "apps.transaction.tests.child_transaction",
            parent_transaction=parent_transaction,
            paid_for=self.user,
            value=Decimal("10.00"),
        )
        baker.make_recipe(
            "apps.transaction.tests.child_transaction",
            parent_transaction=parent_transaction,
            paid_for=self.guest_user,
            value=Decimal("20.00"),
        )

        ordered_children = list(parent_transaction.child_transactions.order_by("-id"))
        data = {
            "description": parent_transaction.description,
            "further_notes": parent_transaction.further_notes or "",
            "paid_by": parent_transaction.paid_by.id,
            "paid_at": parent_transaction.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
            "currency": parent_transaction.currency.id,
            "category": parent_transaction.category.id,
            "paid_for": [child.paid_for.id for child in ordered_children],
            "value": [f"{child.value:.2f}" for child in ordered_children],
            "child_transaction_id": [child.id for child in ordered_children],
            "total_value": "51.01",
        }

        client = self.reauthenticate_user(self.user)
        response = client.post(
            reverse(
                "transaction:edit",
                kwargs={"room_slug": self.room.slug, "pk": parent_transaction.id},
            ),
            data=data,
            follow=True,
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        shares = split_total_across_paid_for(Decimal("51.01"), ordered_children)
        for child, expected in zip(ordered_children, shares, strict=False):
            child.refresh_from_db()
            self.assertEqual(child.value, expected)

        parent_transaction.refresh_from_db()
        self.assertEqual(parent_transaction.value, Decimal("51.01"))
