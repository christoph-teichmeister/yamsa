from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse
from django.utils.datastructures import MultiValueDict
from model_bakery import baker

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import Receipt

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def enforce_media_root(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def _transaction_payload(user, room, currency_id):
    return {
        "description": "Receipt upload",
        "currency": currency_id,
        "paid_at": datetime(2020, 1, 1, 12, 0, tzinfo=UTC),
        "paid_by": user.id,
        "room": room.id,
        "paid_for": [str(user.id) for user in room.users.all()],
        "room_slug": room.slug,
        "value": Decimal("10"),
    }


class TestTransactionReceipt:
    def test_receipt_uploads_with_transaction_and_is_visible(self, authenticated_client, user, room):
        client = authenticated_client
        currency = baker.make_recipe("apps.currency.tests.currency")
        receipt_file = SimpleUploadedFile(
            "receipt.pdf",
            b"%PDF-1.4\n%%EOF",
            content_type="application/pdf",
        )

        payload = {**_transaction_payload(user, room, currency.id), "receipts": receipt_file}

        response = client.post(
            reverse("transaction:create", kwargs={"room_slug": room.slug}),
            data=payload,
            follow=True,
        )

        assert response.status_code == HTTPStatus.OK
        receipt = Receipt.objects.get(parent_transaction__room=room)
        assert receipt.original_name == "receipt.pdf"
        assert receipt.uploaded_by == user
        assert receipt.file.storage.exists(receipt.file.name)

        detail_url = reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": receipt.parent_transaction.pk})
        detail_response = client.get(detail_url)
        assert receipt.original_name in detail_response.content.decode()
        receipt.file.delete(save=False)

    def test_receipt_validation_blocks_unsupported_types(self, user, room):
        currency = baker.make_recipe("apps.currency.tests.currency")
        invalid_file = SimpleUploadedFile(
            "receipt.txt",
            b"not allowed",
            content_type="text/plain",
        )

        payload = {**_transaction_payload(user, room, currency.id), "receipts": invalid_file}

        request = RequestFactory().post("/")
        request.user = user

        files = MultiValueDict({"receipts": [invalid_file]})
        form = TransactionCreateForm(data=payload, files=files, request=request)

        assert not form.is_valid()
        assert "receipts" in form.errors
        assert "Receipts must be PDF or an image" in str(form.errors["receipts"])
