from django.core.files.uploadedfile import SimpleUploadedFile

from apps.transaction.models import Receipt


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
