import mimetypes

from django import forms

from apps.transaction.forms.transaction_create_form import (
    MAX_RECEIPT_SIZE,
    RECEIPT_ACCEPTED_CONTENT_TYPES,
    RECEIPT_AUTH_REQUIRED_MESSAGE,
)
from apps.transaction.models import Receipt

ACCEPTED_RECEIPT_TYPES = ",".join(RECEIPT_ACCEPTED_CONTENT_TYPES)


class TransactionReceiptUploadForm(forms.Form):
    receipt = forms.FileField(
        widget=forms.ClearableFileInput(
            attrs={
                "class": "d-none",
                "accept": ACCEPTED_RECEIPT_TYPES,
            }
        ),
        required=True,
        help_text="Upload a PDF or image (max 5 MB).",
    )

    def __init__(self, *args, request=None, **kwargs):
        self._request = request
        super().__init__(*args, **kwargs)

    def clean_receipt(self):
        uploaded_file = self.cleaned_data.get("receipt")
        if not uploaded_file:
            return uploaded_file

        content_type = getattr(uploaded_file, "content_type", None)
        if not content_type:
            content_type, _ = mimetypes.guess_type(uploaded_file.name)
        if not content_type:
            content_type = "application/octet-stream"
        uploaded_file.content_type = content_type

        if content_type not in RECEIPT_ACCEPTED_CONTENT_TYPES:
            msg = "Receipts must be PDF or an image (PNG, JPEG, WebP, GIF)."
            raise forms.ValidationError(msg, code="invalid_content_type")

        if uploaded_file.size > MAX_RECEIPT_SIZE:
            msg = "Each receipt must be 5 MB or smaller."
            raise forms.ValidationError(msg, code="file_too_large")

        uploader = getattr(self._request, "user", None)
        if not uploader or not uploader.is_authenticated:
            raise forms.ValidationError(RECEIPT_AUTH_REQUIRED_MESSAGE, code="authentication_required")

        return uploaded_file

    def save(self, parent_transaction):
        receipt_file = self.cleaned_data["receipt"]
        uploader = getattr(self._request, "user", None)
        return Receipt.objects.create(
            parent_transaction=parent_transaction,
            file=receipt_file,
            original_name=receipt_file.name,
            content_type=receipt_file.content_type,
            size=receipt_file.size,
            uploaded_by=uploader,
        )
