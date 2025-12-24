import http
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.transaction.models import ChildTransaction
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.factories import ParentTransactionFactory
from apps.transaction.utils import split_total_across_paid_for

pytestmark = pytest.mark.django_db


class TestTransactionEditView:
    def test_post_rebalances_child_transactions_when_total_changes(self, authenticated_client, room, user, guest_user):
        parent_transaction = ParentTransactionFactory(room=room, paid_by=user)
        default_category = RoomCategoryService(room=room).get_default_category()
        if default_category:
            parent_transaction.category = default_category
            parent_transaction.save(update_fields=("category",))
        ChildTransaction.objects.create(
            parent_transaction=parent_transaction,
            paid_for=user,
            value=Decimal("10.00"),
        )
        ChildTransaction.objects.create(
            parent_transaction=parent_transaction,
            paid_for=guest_user,
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

        response = authenticated_client.post(
            reverse(
                "transaction:edit",
                kwargs={"room_slug": room.slug, "pk": parent_transaction.id},
            ),
            data=data,
            follow=True,
        )

        assert response.status_code == http.HTTPStatus.OK

        shares = split_total_across_paid_for(Decimal("51.01"), ordered_children)
        for child, expected in zip(ordered_children, shares, strict=False):
            child.refresh_from_db()
            assert child.value == expected

        parent_transaction.refresh_from_db()
        assert parent_transaction.value == Decimal("51.01")
