import pytest

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import Category
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db


class TestTransactionFormStructure:
    def test_create_form_exposes_category_field_ordered(self):
        form = TransactionCreateForm()
        assert "category" in form.fields

        queryset = form.fields["category"].queryset
        slugs = {category.slug for category in queryset}
        assert "accommodation" in slugs

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
