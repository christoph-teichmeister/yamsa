import os
import shutil
import tempfile
from datetime import UTC, datetime
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.transaction.models import Receipt


class TransactionReceiptTest(BaseTestSetUp):
    def setUp(self):
        super().setUp()
        self._media_root = tempfile.mkdtemp()
        self._media_override = self.settings(MEDIA_ROOT=self._media_root)
        self._media_override.enable()

    def tearDown(self):
        self._media_override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)
        super().tearDown()

    def _transaction_payload(self, currency_id):
        return {
            "description": "Receipt upload",
            "currency": currency_id,
            "paid_at": datetime(2020, 1, 1, 12, 0, tzinfo=UTC),
            "paid_by": self.user.id,
            "room": self.room.id,
            "paid_for": [str(user.id) for user in self.room.users.all()],
            "room_slug": self.room.slug,
            "value": 10,
        }

    def test_receipt_uploads_with_transaction_and_is_visible(self):
        client = self.reauthenticate_user(self.user)
        currency = baker.make_recipe("apps.currency.tests.currency")
        receipt_file = SimpleUploadedFile(
            "receipt.pdf",
            b"%PDF-1.4\n%%EOF",
            content_type="application/pdf",
        )

        response = client.post(
            reverse("transaction:create", kwargs={"room_slug": self.room.slug}),
            data={**self._transaction_payload(currency.id)},
            files={"receipts": receipt_file},
            follow=True,
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        receipt = Receipt.objects.get(parent_transaction__room=self.room)
        self.assertEqual(receipt.original_name, "receipt.pdf")
        self.assertEqual(receipt.uploaded_by, self.user)
        self.assertTrue(os.path.exists(receipt.file.path))

        detail_url = reverse(
            "transaction:detail", kwargs={"room_slug": self.room.slug, "pk": receipt.parent_transaction.pk}
        )
        detail_response = client.get(detail_url)
        self.assertContains(detail_response, receipt.original_name)
        receipt.file.delete(save=False)

    def test_receipt_validation_blocks_unsupported_types(self):
        client = self.reauthenticate_user(self.user)
        currency = baker.make_recipe("apps.currency.tests.currency")
        invalid_file = SimpleUploadedFile(
            "receipt.txt",
            b"not allowed",
            content_type="text/plain",
        )

        response = client.post(
            reverse("transaction:create", kwargs={"room_slug": self.room.slug}),
            data={**self._transaction_payload(currency.id)},
            files={"receipts": invalid_file},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        form = response.context_data["form"]
        self.assertIn("receipts", form.errors)
        self.assertIn("Receipts must be PDF or an image", str(form.errors["receipts"]))
