from unittest.mock import MagicMock

import pytest

from apps.account.tests.factories import UserFactory
from apps.currency.tests.factories import CurrencyFactory
from apps.room.tests.factories import RoomFactory
from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import Category, ParentTransaction
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
        from apps.transaction.forms.transaction_edit_form import TransactionEditForm

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

    def _build_create_form_data(self, room, user, currency, paid_for_users, description="Test transaction"):
        from django.utils import timezone

        return {
            "description": description,
            "currency": currency.id,
            "paid_at": timezone.now(),
            "paid_by": user.id,
            "room": room.id,
            "paid_for": [u.id for u in paid_for_users],
            "room_slug": room.slug,
            "value": "12.00",
        }

    def test_save_two_consecutive_transactions_both_persist(self):
        """
        Regression test for #333: two consecutive saves must both succeed.
        Previously the second failed because the DB connection was blocked by
        a webpush HTTP call inside the open atomic block.
        """
        user = UserFactory()
        other_user = UserFactory()
        room = RoomFactory(created_by=user)
        room.users.add(user, other_user)
        currency = CurrencyFactory()
        request_mock = MagicMock(user=user)

        for i in range(2):
            form_data = self._build_create_form_data(
                room, user, currency, [user, other_user], description=f"Transaction {i}"
            )
            form = TransactionCreateForm(data=form_data, request=request_mock, room=room)
            assert form.is_valid(), f"Form {i} invalid: {form.errors}"
            form.save()

        assert ParentTransaction.objects.filter(room=room).count() == 2
