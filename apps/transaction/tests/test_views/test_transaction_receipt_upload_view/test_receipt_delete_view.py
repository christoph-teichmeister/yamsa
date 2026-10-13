import json
from collections.abc import Iterator
from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.core.toast_constants import SUCCESS_TOAST_CLASS
from apps.room.models import Room
from apps.transaction.models import ParentTransaction, Receipt
from apps.transaction.tests.test_views.test_transaction_receipt_upload_view.test_helpers import create_receipt

pytestmark = pytest.mark.django_db


@pytest.fixture
def receipt_for_guest(transaction_with_children: ParentTransaction, guest_user: User) -> Iterator[Receipt]:
    receipt = create_receipt(transaction_with_children, uploaded_by=guest_user)
    try:
        yield receipt
    finally:
        receipt.file.delete(save=False)
        Receipt.objects.filter(pk=receipt.pk).delete()


class TestTransactionReceiptDeleteView:
    def test_receipt_owner_can_delete_receipt(
        self, authenticated_client: Client, room: Room, user: User, transaction_with_children: ParentTransaction
    ) -> None:
        parent_transaction = transaction_with_children
        receipt = create_receipt(parent_transaction, uploaded_by=user)

        response = authenticated_client.post(
            reverse("transaction:receipt-delete", kwargs={"room_slug": room.slug, "receipt_pk": receipt.id})
        )

        assert response.status_code == HTTPStatus.OK
        assert not Receipt.objects.filter(pk=receipt.pk).exists()
        assert "HX-Trigger" in response.headers
        trigger_payload = json.loads(response.headers["HX-Trigger"])
        toasts = trigger_payload["triggerToast"]
        assert isinstance(toasts, list)
        assert toasts[0]["message"] == "Receipt deleted."
        assert toasts[0]["type"] == SUCCESS_TOAST_CLASS
        assert receipt.original_name not in response.content.decode()

    def test_receipt_delete_forbidden_for_other_user(
        self, authenticated_client: Client, room: Room, guest_user: User, receipt_for_guest: Receipt
    ) -> None:
        receipt = receipt_for_guest

        response = authenticated_client.post(
            reverse("transaction:receipt-delete", kwargs={"room_slug": room.slug, "receipt_pk": receipt.id})
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert Receipt.objects.filter(pk=receipt.pk).exists()

    def test_receipt_delete_rejected_for_closed_room(
        self,
        authenticated_client: Client,
        closed_room: Room,
        user: User,
        transaction_with_children_in_closed_room: ParentTransaction,
    ) -> None:
        receipt = create_receipt(transaction_with_children_in_closed_room, uploaded_by=user)

        response = authenticated_client.post(
            reverse("transaction:receipt-delete", kwargs={"room_slug": closed_room.slug, "receipt_pk": receipt.id})
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert Receipt.objects.filter(pk=receipt.pk).exists()
