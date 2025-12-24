from decimal import Decimal
from typing import Any

import pytest

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import Category, ChildTransaction
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


class TestTransactionFormStructure:
    def test_create_form_exposes_category_field_ordered(self):
        form = TransactionCreateForm()
        assert "category" in form.fields

        queryset = list(form.fields["category"].queryset)
        assert len(queryset) >= 1
        assert queryset[0].slug == "accommodation"

    def test_edit_form_initial_category_matches_instance(self):
        category = Category.objects.get(slug="groceries")
        parent_transaction = ParentTransactionFactory(category=category)
        form = TransactionEditForm(instance=parent_transaction)

        assert form.initial["category"] == category.pk

    def test_create_form_respects_room_specific_categories(self, room):
        service = RoomCategoryService(room=room)
        service.create_room_category(name="House Tag", emoji="🏠", color="#123456")
        form = TransactionCreateForm(room=room)

        slugs = [category.slug for category in form.fields["category"].queryset]
        assert any(slug.startswith("house-tag") for slug in slugs)


@pytest.fixture
def parent_transaction_with_children(room, guest_user, user):
    parent_transaction = ParentTransactionFactory(room=room, paid_by=user)
    first_child = ChildTransaction.objects.create(
        parent_transaction=parent_transaction,
        paid_for=user,
        value=Decimal("10.00"),
    )
    second_child = ChildTransaction.objects.create(
        parent_transaction=parent_transaction,
        paid_for=guest_user,
        value=Decimal("20.00"),
    )
    default_category = RoomCategoryService(room=room).get_default_category()
    if default_category:
        parent_transaction.category = default_category
        parent_transaction.save(update_fields=("category",))
    return parent_transaction, [first_child, second_child]


def _base_form_data(parent_transaction, total_value) -> dict[str, Any]:
    child_transactions = list(parent_transaction.child_transactions.order_by("-id"))
    return {
        "description": parent_transaction.description,
        "further_notes": parent_transaction.further_notes or "",
        "paid_by": parent_transaction.paid_by.id,
        "paid_at": parent_transaction.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
        "currency": parent_transaction.currency.id,
        "category": parent_transaction.category.id,
        "paid_for": [ct.paid_for.id for ct in child_transactions],
        "value": [str(ct.value) for ct in child_transactions],
        "child_transaction_id": [ct.id for ct in child_transactions],
        "total_value": total_value,
    }


class TestTransactionEditFormTotalValue:
    def test_total_value_field_exposes_correct_initial(self, parent_transaction_with_children):
        parent_transaction, _ = parent_transaction_with_children
        form = TransactionEditForm(instance=parent_transaction)

        assert "total_value" in form.fields
        assert form.initial["total_value"] == parent_transaction.value

    def test_rebalances_shares_when_total_changes(self, parent_transaction_with_children):
        parent_transaction, _ = parent_transaction_with_children
        data = _base_form_data(parent_transaction, total_value="60.00")
        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert form.is_valid()
        assert form.cleaned_data["total_value"] == Decimal("60.00")
        assert form.cleaned_data["value"] == [Decimal("30.00"), Decimal("30.00")]

    def test_propagates_value_sum_when_shares_rebalanced(self, parent_transaction_with_children):
        parent_transaction, _ = parent_transaction_with_children
        data = _base_form_data(parent_transaction, total_value=str(parent_transaction.value))
        data["value"] = ["15.00", "25.00"]
        form = TransactionEditForm(data=data, instance=parent_transaction)

        assert form.is_valid()
        assert form.cleaned_data["total_value"] == Decimal("40.00")
        assert form.cleaned_data["value"] == [Decimal("15.00"), Decimal("25.00")]
