from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.models import Category, ChildTransaction, ParentTransaction
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.factories import ParentTransactionFactory

PAID_AT = datetime(2026, 3, 14, 12, 0, tzinfo=UTC)


@pytest.fixture
def parent_transaction(room: Room, user: User, guest_user: User) -> ParentTransaction:
    parent = ParentTransactionFactory(room=room, paid_by=user)
    ChildTransaction.objects.create(parent_transaction=parent, paid_for=user, value=Decimal("10.00"))
    ChildTransaction.objects.create(parent_transaction=parent, paid_for=guest_user, value=Decimal("20.00"))
    default_category = RoomCategoryService(room=room).get_default_category()
    if default_category:
        parent.category = default_category
        parent.save(update_fields=("category",))
    return parent


def edit_data(parent: ParentTransaction, **overrides: Any) -> dict[str, Any]:  # noqa: ANN401
    children = list(parent.child_transactions.order_by("id"))
    data = {
        "description": parent.description,
        "further_notes": "",
        "paid_by": parent.paid_by_id,
        "paid_at": parent.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
        "currency": parent.currency_id,
        "category": parent.category_id,
        "paid_for": [child.paid_for_id for child in children],
        "value": [str(child.value) for child in children],
        "child_transaction_id": [child.id for child in children],
        "total_value": str(parent.value),
    }
    data.update(overrides)
    return data


def create_data(room: Room, user: User, paid_for: list[int], values: list[str], total: str) -> dict[str, Any]:
    return {
        "description": "Dinner",
        "further_notes": "",
        "paid_by": user.id,
        "paid_at": PAID_AT.strftime("%Y-%m-%d %H:%M:%S"),
        "currency": room.preferred_currency.id,
        "category": Category.objects.get(slug="groceries").id,
        "room": room.id,
        "room_slug": room.slug,
        "paid_for": paid_for,
        "value": values,
        "total_value": total,
        "reference_total_value": total,
    }
