import json
from http import HTTPStatus

import pytest
from django.urls import reverse

from apps.core.toast_constants import SUCCESS_TOAST_CLASS
from apps.transaction.models import Receipt

from .helpers import create_receipt

pytestmark = pytest.mark.django_db


class TestTransactionReceiptDeleteView:
    def test_receipt_owner_can_delete_receipt(self, authenticated_client, room, user, transaction_with_children):
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
        self, authenticated_client, room, guest_user, transaction_with_children
    ):
        parent_transaction = transaction_with_children
        receipt = create_receipt(parent_transaction, uploaded_by=guest_user)

        response = authenticated_client.post(
            reverse("transaction:receipt-delete", kwargs={"room_slug": room.slug, "receipt_pk": receipt.id})
        )

        assert response.status_code == HTTPStatus.FORBIDDEN
        assert Receipt.objects.filter(pk=receipt.pk).exists()
        receipt.file.delete(save=False)
        receipt.delete()
