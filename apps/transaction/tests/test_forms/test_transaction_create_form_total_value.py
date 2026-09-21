from decimal import Decimal
from typing import Any

import pytest
from django.utils import timezone

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import Category

pytestmark = pytest.mark.django_db


def _base_form_data(room, user, guest_user, total_value, values, reference_total_value=None) -> dict[str, Any]:
    data = {
        "description": "Dinner",
        "further_notes": "",
        "paid_by": user.id,
        "paid_at": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
        "currency": room.preferred_currency.id,
        "category": Category.objects.get(slug="groceries").id,
        "room": room.id,
        "room_slug": room.slug,
        "paid_for": [user.id, guest_user.id],
        "value": values,
        "total_value": total_value,
    }
    if reference_total_value is not None:
        data["reference_total_value"] = reference_total_value
    return data


class TestTransactionCreateFormTotalValue:
    def test_splits_evenly_when_no_reference_is_given(self, room, user, guest_user):
        data = _base_form_data(room, user, guest_user, total_value="90.00", values=["0.00", "0.00"])
        form = TransactionCreateForm(data=data, request=None, room=room)

        assert form.is_valid(), form.errors
        assert form.cleaned_data["value"] == [Decimal("45.00"), Decimal("45.00")]

    def test_honours_manual_shares_when_total_matches_reference(self, room, user, guest_user):
        data = _base_form_data(
            room,
            user,
            guest_user,
            total_value="90.00",
            values=["80.00", "10.00"],
            reference_total_value="90.00",
        )
        form = TransactionCreateForm(data=data, request=None, room=room)

        assert form.is_valid(), form.errors
        assert form.cleaned_data["value"] == [Decimal("80.00"), Decimal("10.00")]
        assert form.cleaned_data["total_value"] == Decimal("90.00")

    def test_rebalances_shares_when_total_differs_from_reference(self, room, user, guest_user):
        data = _base_form_data(
            room,
            user,
            guest_user,
            total_value="100.00",
            values=["80.00", "10.00"],
            reference_total_value="90.00",
        )
        form = TransactionCreateForm(data=data, request=None, room=room)

        assert form.is_valid(), form.errors
        assert form.cleaned_data["value"] == [Decimal("50.00"), Decimal("50.00")]

    def test_propagates_value_sum_when_manual_shares_do_not_match_total(self, room, user, guest_user):
        data = _base_form_data(
            room,
            user,
            guest_user,
            total_value="90.00",
            values=["30.00", "10.00"],
            reference_total_value="90.00",
        )
        form = TransactionCreateForm(data=data, request=None, room=room)

        assert form.is_valid(), form.errors
        assert form.cleaned_data["total_value"] == Decimal("40.00")
        assert form.cleaned_data["value"] == [Decimal("30.00"), Decimal("10.00")]
