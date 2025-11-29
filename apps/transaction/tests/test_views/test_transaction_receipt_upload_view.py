import json
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker

from apps.core.toast_constants import SUCCESS_TOAST_CLASS
from apps.transaction.models import Receipt

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enforce_media_root(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def transaction_with_children(room, user):
    parent_transaction = baker.make_recipe(
        "apps.transaction.tests.parent_transaction",
        room=room,
        paid_by=user,
        currency=room.preferred_currency,
    )

    for member in room.users.all():
        baker.make_recipe(
            "apps.transaction.tests.child_transaction",
            parent_transaction=parent_transaction,
            paid_for=member,
            value=Decimal("5"),
        )

    return parent_transaction


def create_receipt(parent_transaction, uploaded_by):
    receipt_file = SimpleUploadedFile(
        "receipt.pdf",
        b"%PDF-1.4\n%%EOF",
        content_type="application/pdf",
    )
    return Receipt.objects.create(
        parent_transaction=parent_transaction,
        file=receipt_file,
        original_name="receipt.pdf",
        content_type="application/pdf",
        size=receipt_file.size,
        uploaded_by=uploaded_by,
    )


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
