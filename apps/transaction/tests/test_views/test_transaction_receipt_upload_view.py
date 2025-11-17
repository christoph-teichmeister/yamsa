import json
import shutil
import tempfile
from decimal import Decimal
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker

from apps.core.tests.setup import BaseTestSetUp
from apps.core.toast_constants import SUCCESS_TOAST_CLASS
from apps.transaction.models import Receipt


class TransactionReceiptViewBaseTest(BaseTestSetUp):
    def setUp(self):
        super().setUp()
        self._media_root = tempfile.mkdtemp()
        self._media_override = self.settings(MEDIA_ROOT=self._media_root)
        self._media_override.enable()

    def tearDown(self):
        self._media_override.disable()
        shutil.rmtree(self._media_root, ignore_errors=True)
        super().tearDown()

    def _build_transaction(self):
        parent_transaction = baker.make_recipe(
            "apps.transaction.tests.parent_transaction",
            room=self.room,
            paid_by=self.user,
            currency=self.room.preferred_currency,
        )
        for user in self.room.users.all():
            baker.make_recipe(
                "apps.transaction.tests.child_transaction",
                parent_transaction=parent_transaction,
                paid_for=user,
                value=Decimal("5"),
            )
        return parent_transaction


class TransactionReceiptUploadViewTest(TransactionReceiptViewBaseTest):
    def test_receipt_uploads_for_transaction_detail(self):
        client = self.reauthenticate_user(self.user)
        parent_transaction = self._build_transaction()
        receipt_file = SimpleUploadedFile(
            "receipt.pdf",
            b"%PDF-1.4\n%%EOF",
            content_type="application/pdf",
        )

        response = client.post(
            reverse("transaction:receipt-upload", kwargs={"room_slug": self.room.slug, "pk": parent_transaction.id}),
            data={"receipt": receipt_file},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        receipt = Receipt.objects.get(parent_transaction=parent_transaction)
        self.assertEqual(receipt.original_name, "receipt.pdf")
        self.assertEqual(receipt.uploaded_by, self.user)
        self.assertContains(response, receipt.original_name)
        self.assertIn("HX-Trigger", response.headers)
        self.assertIn("HX-Trigger-After-Settle", response.headers)
        trigger_payload = json.loads(response.headers["HX-Trigger"])
        self.assertEqual(trigger_payload["triggerToast"]["message"], "Receipt uploaded successfully.")
        self.assertEqual(trigger_payload["triggerToast"]["type"], SUCCESS_TOAST_CLASS)
        receipt.file.delete(save=False)

    def test_receipt_upload_rejects_invalid_file(self):
        client = self.reauthenticate_user(self.user)
        parent_transaction = self._build_transaction()
        invalid_file = SimpleUploadedFile(
            "receipt.txt",
            b"not allowed",
            content_type="text/plain",
        )

        response = client.post(
            reverse("transaction:receipt-upload", kwargs={"room_slug": self.room.slug, "pk": parent_transaction.id}),
            data={"receipt": invalid_file},
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, "Receipts must be PDF or an image")
        self.assertFalse(Receipt.objects.filter(parent_transaction=parent_transaction).exists())
        self.assertNotIn("HX-Trigger-After-Settle", response.headers)
        self.assertNotIn("HX-Trigger", response.headers)


class TransactionReceiptDeleteViewTest(TransactionReceiptViewBaseTest):
    def _create_receipt(self, parent_transaction, uploaded_by):
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

    def test_receipt_owner_can_delete_receipt(self):
        client = self.reauthenticate_user(self.user)
        parent_transaction = self._build_transaction()
        receipt = self._create_receipt(parent_transaction, self.user)

        response = client.post(
            reverse("transaction:receipt-delete", kwargs={"room_slug": self.room.slug, "pk": receipt.id})
        )

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Receipt.objects.filter(pk=receipt.pk).exists())
        self.assertNotContains(response, receipt.original_name)
        self.assertIn("HX-Trigger", response.headers)
        trigger_payload = json.loads(response.headers["HX-Trigger"])
        self.assertEqual(trigger_payload["triggerToast"]["message"], "Receipt deleted.")

    def test_receipt_delete_forbidden_for_other_user(self):
        client = self.reauthenticate_user(self.user)
        parent_transaction = self._build_transaction()
        receipt = self._create_receipt(parent_transaction, self.guest_user)

        response = client.post(
            reverse("transaction:receipt-delete", kwargs={"room_slug": self.room.slug, "pk": receipt.id})
        )

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(Receipt.objects.filter(pk=receipt.pk).exists())
        receipt.file.delete(save=False)
        receipt.delete()
