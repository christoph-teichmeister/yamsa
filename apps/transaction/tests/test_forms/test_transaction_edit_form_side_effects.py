from decimal import Decimal
from unittest import mock

import pytest
from django.urls import reverse

from apps.transaction.forms.transaction_edit_form import TransactionEditForm
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.tests.factories import ParentTransactionFactory

pytestmark = pytest.mark.django_db

DEBT_RECALCULATION = "apps.debt.handlers.events.optimise_debts.DebtOptimiseService.process"


@pytest.fixture
def parent_transaction(room, user, guest_user) -> ParentTransaction:
    parent_transaction = ParentTransactionFactory(
        room=room, paid_by=user, category=RoomCategoryService(room=room).get_default_category()
    )
    for participant in (user, guest_user):
        ChildTransaction.objects.create(parent_transaction=parent_transaction, paid_for=participant, value="15.00")
    return parent_transaction


def _form_data(parent_transaction, *, values: list[str]) -> dict:
    child_transactions = list(parent_transaction.child_transactions.order_by("id"))
    return {
        "description": parent_transaction.description,
        "further_notes": "",
        "paid_by": parent_transaction.paid_by.id,
        "paid_at": parent_transaction.paid_at.strftime("%Y-%m-%d %H:%M:%S"),
        "currency": parent_transaction.currency.id,
        "category": parent_transaction.category.id,
        "paid_for": [child.paid_for.id for child in child_transactions],
        "value": values,
        "child_transaction_id": [child.id for child in child_transactions],
        "total_value": str(sum((Decimal(value) for value in values), Decimal("0.00"))),
    }


class TestTransactionEditFormSideEffects:
    def test_saving_the_form_only_persists(self, parent_transaction) -> None:
        form = TransactionEditForm(
            data=_form_data(parent_transaction, values=["10.00", "20.00"]), instance=parent_transaction
        )
        assert form.is_valid(), form.errors

        with mock.patch(DEBT_RECALCULATION) as recalculate:
            form.save()

        # The event, and the debt recalculation it triggers, are the view's to send (AGENTS.md).
        recalculate.assert_not_called()
        assert sorted(parent_transaction.child_transactions.values_list("value", flat=True)) == [
            Decimal("10.00"),
            Decimal("20.00"),
        ]

    def test_saving_through_the_view_recalculates_the_debts(
        self, authenticated_client, room, parent_transaction
    ) -> None:
        with mock.patch(DEBT_RECALCULATION) as recalculate:
            response = authenticated_client.post(
                reverse("transaction:edit", kwargs={"room_slug": room.slug, "pk": parent_transaction.id}),
                data=_form_data(parent_transaction, values=["10.00", "20.00"]),
            )

        assert response.status_code == 302
        recalculate.assert_called_once_with(room_id=room.id)
