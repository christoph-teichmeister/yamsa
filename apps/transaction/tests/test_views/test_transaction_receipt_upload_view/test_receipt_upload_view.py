import json
from http import HTTPStatus

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.core.toast_constants import SUCCESS_TOAST_CLASS
from apps.transaction.models import Receipt

pytestmark = pytest.mark.django_db


class TestTransactionReceiptUploadView:
    def test_receipt_uploads_for_transaction_detail(self, authenticated_client, room, user, transaction_with_children):
        parent_transaction = transaction_with_children
        receipt_file = SimpleUploadedFile(
            "receipt.pdf",
            b"%PDF-1.4\n%%EOF",
            content_type="application/pdf",
        )

        response = authenticated_client.post(
            reverse(
                "transaction:receipt-upload",
                kwargs={"room_slug": room.slug, "transaction_pk": parent_transaction.id},
            ),
            data={"receipt": receipt_file},
        )

        assert response.status_code == HTTPStatus.OK
        receipt = Receipt.objects.get(parent_transaction=parent_transaction)
        assert receipt.original_name == "receipt.pdf"
        assert receipt.uploaded_by == user
        assert "HX-Trigger" in response.headers
        assert "HX-Trigger-After-Settle" in response.headers
        trigger_payload = json.loads(response.headers["HX-Trigger"])
        toasts = trigger_payload["triggerToast"]
        assert isinstance(toasts, list)
        assert toasts[0]["message"] == "Receipt uploaded successfully."
        assert toasts[0]["type"] == SUCCESS_TOAST_CLASS
        assert receipt.original_name in response.content.decode()
        receipt.file.delete(save=False)

    def test_receipt_upload_rejects_invalid_file(self, authenticated_client, room, transaction_with_children):
        parent_transaction = transaction_with_children
        invalid_file = SimpleUploadedFile(
            "receipt.txt",
            b"not allowed",
            content_type="text/plain",
        )

        response = authenticated_client.post(
            reverse(
                "transaction:receipt-upload",
                kwargs={"room_slug": room.slug, "transaction_pk": parent_transaction.id},
            ),
            data={"receipt": invalid_file},
        )

        assert response.status_code == HTTPStatus.OK
        assert "Receipts must be PDF or an image" in response.content.decode()
        assert not Receipt.objects.filter(parent_transaction=parent_transaction).exists()
        assert "HX-Trigger-After-Settle" not in response.headers
        assert "HX-Trigger" not in response.headers
