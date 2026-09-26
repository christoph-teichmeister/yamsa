import base64

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse

from apps.room.models import Room
from apps.transaction.models import Receipt
from apps.transaction.tests.factories import ParentTransactionFactory
from e2e.pages.transaction_detail_page import TransactionDetailPage

# The smallest valid PNG (1x1, transparent), so the upload is a real image and not merely named one.
ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


@pytest.fixture
def parent_transaction(room, profile_user):
    return ParentTransactionFactory(
        room=room, paid_by=profile_user, currency=room.preferred_currency, description="Baumarkt"
    )


@pytest.fixture
def open_detail(page, base_url, room, parent_transaction, logged_in):
    def _open() -> TransactionDetailPage:
        logged_in()
        detail_page = TransactionDetailPage(
            page,
            base_url,
            reverse("transaction:detail", kwargs={"room_slug": room.slug, "pk": parent_transaction.id}),
        )
        detail_page.navigate()
        return detail_page

    return _open


@pytest.mark.e2e
class TestTransactionReceipts:
    def test_an_uploaded_receipt_is_attached_to_the_transaction(self, open_detail, parent_transaction, profile_user):
        detail_page = open_detail()
        detail_page.expect_no_receipts()

        detail_page.upload_receipt(name="kassenbon.png", mime_type="image/png", content=ONE_PIXEL_PNG)

        detail_page.expect_receipt("kassenbon.png")
        receipt = Receipt.objects.get(parent_transaction=parent_transaction)
        assert (receipt.original_name, receipt.content_type, receipt.uploaded_by) == (
            "kassenbon.png",
            "image/png",
            profile_user,
        )

    def test_a_file_that_is_no_receipt_is_rejected(self, open_detail, parent_transaction):
        detail_page = open_detail()

        detail_page.upload_receipt(name="notizen.txt", mime_type="text/plain", content=b"keine Quittung")

        detail_page.expect_receipt_error("Receipts must be PDF or an image")
        detail_page.expect_no_receipts()
        assert not Receipt.objects.filter(parent_transaction=parent_transaction).exists()

    def test_the_uploader_can_delete_their_receipt(self, open_detail, parent_transaction):
        detail_page = open_detail()
        detail_page.upload_receipt(name="kassenbon.png", mime_type="image/png", content=ONE_PIXEL_PNG)
        detail_page.expect_receipt("kassenbon.png")

        detail_page.delete_receipt("kassenbon.png")

        detail_page.expect_no_receipts()
        assert not Receipt.objects.filter(parent_transaction=parent_transaction).exists()

    def test_a_roommates_receipt_cannot_be_deleted(self, open_detail, parent_transaction, roommate):
        Receipt.objects.create(
            parent_transaction=parent_transaction,
            file=ContentFile(ONE_PIXEL_PNG, name="von-mitbewohner.png"),
            original_name="von-mitbewohner.png",
            content_type="image/png",
            size=len(ONE_PIXEL_PNG),
            uploaded_by=roommate,
        )
        detail_page = open_detail()

        detail_page.expect_receipt("von-mitbewohner.png")
        detail_page.expect_receipt_not_deletable("von-mitbewohner.png")

    def test_a_closed_room_takes_no_more_receipts(self, open_detail, room):
        Room.objects.filter(id=room.id).update(status=Room.StatusChoices.CLOSED)

        detail_page = open_detail()

        detail_page.expect_upload_closed()
