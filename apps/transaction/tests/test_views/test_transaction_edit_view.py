import http
import re
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import ChildTransaction
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.factories import ParentTransactionFactory
from apps.transaction.utils import split_total_across_paid_for

pytestmark = pytest.mark.django_db


def _extract_total_input_attributes(response):
    response_html = response.content.decode()
    input_tag_match = re.search(r'<input\b[^>]*id=(?:["\']?)total_value_input(?:["\']?)[^>]*>', response_html, re.S)
    if not input_tag_match:
        error_msg = (
            "Unable to locate the total value input in the edit form response. "
            f"Response snippet:\n{response_html[:4000]}"
        )
        raise AssertionError(error_msg)

    input_tag = input_tag_match.group(0)
    value_match = re.search(r'value=(?:["\']?)([^"\'>\s]*)(?:["\']?)', input_tag)
    initial_match = re.search(r'data-initial-total=(?:["\']?)([^"\'>\s]*)(?:["\']?)', input_tag)

    assert value_match and initial_match, "Expected both value and data-initial-total attributes on the total input."

    return value_match.group(1), initial_match.group(1)


def _request_total_input_attributes(
    authenticated_client,
    room,
    user,
    guest_user,
    monkeypatch,
    initial_total_override,
    child_total_value=None,
):
    parent_transaction = ParentTransactionFactory(room=room, paid_by=user)
    if child_total_value is not None:
        ChildTransaction.objects.create(
            parent_transaction=parent_transaction,
            paid_for=guest_user,
            value=child_total_value,
        )

    monkeypatch.setattr(
        TransactionEditForm,
        "_current_total_value",
        lambda self: initial_total_override,
    )

    response = authenticated_client.get(
        reverse(
            "transaction:edit",
            kwargs={"room_slug": room.slug, "pk": parent_transaction.id},
        )
    )
    assert response.status_code == http.HTTPStatus.OK
    return _extract_total_input_attributes(response)


_INITIAL_TOTAL_VARIATIONS = [
    (None, Decimal("12.34"), "12.34"),
    (0, None, "0.00"),
    ("", None, "0.00"),
]


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

    @pytest.mark.parametrize(
        "initial_total_override, child_total_value, expected_formatted",
        _INITIAL_TOTAL_VARIATIONS,
    )
    def test_total_input_formats_edge_initial_totals(
        self,
        authenticated_client,
        room,
        user,
        guest_user,
        monkeypatch,
        initial_total_override,
        child_total_value,
        expected_formatted,
    ):
        """Settlement-critical totals must re-render as two-decimal strings even when the form's stored total arrives
        as None, zero, or empty."""
        value_attr, sanitized_initial = _request_total_input_attributes(
            authenticated_client,
            room,
            user,
            guest_user,
            monkeypatch,
            initial_total_override,
            child_total_value,
        )
        assert value_attr == expected_formatted
        assert sanitized_initial == expected_formatted

    @pytest.mark.parametrize(
        "initial_total_override, child_total_value, expected_formatted",
        _INITIAL_TOTAL_VARIATIONS,
    )
    def test_lock_state_dataset_matches_formatted_total(
        self,
        authenticated_client,
        room,
        user,
        guest_user,
        monkeypatch,
        initial_total_override,
        child_total_value,
        expected_formatted,
    ):
        """The lock-state script (Safari/Augmented iOS flow) reads the formatted dataset, so it must match the
        rendered total for these edge cases."""
        value_attr, sanitized_initial = _request_total_input_attributes(
            authenticated_client,
            room,
            user,
            guest_user,
            monkeypatch,
            initial_total_override,
            child_total_value,
        )
        assert value_attr == sanitized_initial == expected_formatted
