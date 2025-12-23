import mimetypes
from decimal import Decimal

from django import forms
from django.db import transaction

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionCreated
from apps.transaction.models import Category, ChildTransaction, ParentTransaction, Receipt
from apps.transaction.services.room_category_service import RoomCategoryService
from apps.transaction.utils import split_total_across_paid_for

RECEIPT_ACCEPTED_CONTENT_TYPES = (
    "application/pdf",
    "image/gif",
    "image/jpeg",
    "image/png",
    "image/webp",
)
MAX_RECEIPT_SIZE = 5 * 1024 * 1024  # 5 MB
RECEIPT_AUTH_REQUIRED_MESSAGE = "Authenticated user is required to upload receipts."


class TransactionCreateForm(forms.ModelForm):
    paid_for = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    room_slug = forms.CharField()
    value = forms.DecimalField()
    category = forms.ModelChoiceField(
        queryset=Category.objects.order_by("order_index", "id"),
        empty_label=None,
        required=False,
    )
    receipts = forms.FileField(
        widget=forms.ClearableFileInput(),
        required=False,
        help_text="Upload PNG/JPEG/WebP/GIF images or PDFs (max 5 MB each).",
    )

    class Meta:
        model = ParentTransaction
        fields = (
            "description",
            "further_notes",
            "currency",
            "paid_by",
            "paid_at",
            "room",
            "paid_for",
            "room_slug",
            "value",
            "category",
        )

    def __init__(self, *args, request=None, room=None, **kwargs):
        self._request = request
        self._room = room
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = self._build_category_queryset()

    def clean_receipts(self):
        field_name = self.add_prefix("receipts")
        uploaded_files = self.files.getlist(field_name)
        cleaned_files = []
        errors = []

        for uploaded_file in uploaded_files:
            content_type = getattr(uploaded_file, "content_type", None)
            if not content_type:
                content_type, _ = mimetypes.guess_type(uploaded_file.name)
            if not content_type:
                content_type = "application/octet-stream"
            uploaded_file.content_type = content_type

            file_errors = []

            if content_type not in RECEIPT_ACCEPTED_CONTENT_TYPES:
                file_errors.append(
                    forms.ValidationError(
                        "Receipts must be PDF or an image (PNG, JPEG, WebP, GIF).",
                        code="invalid_content_type",
                    )
                )

            if uploaded_file.size > MAX_RECEIPT_SIZE:
                file_errors.append(
                    forms.ValidationError("Each receipt must be 5 MB or smaller.", code="file_too_large")
                )

            if file_errors:
                errors.extend(file_errors)
            else:
                cleaned_files.append(uploaded_file)

        if errors:
            raise forms.ValidationError(errors)

        if cleaned_files:
            uploader = getattr(self._request, "user", None)
            if not uploader or not uploader.is_authenticated:
                raise forms.ValidationError(
                    RECEIPT_AUTH_REQUIRED_MESSAGE,
                    code="authentication_required",
                )

        return cleaned_files

    @transaction.atomic
    def save(self, commit=True):
        instance: ParentTransaction = super().save(commit)

        total_value = Decimal(self.cleaned_data["value"])
        paid_for_entries = list(self.cleaned_data["paid_for"])
        shares = split_total_across_paid_for(total_value, paid_for_entries)
        for debtor, share in zip(paid_for_entries, shares, strict=False):
            ChildTransaction.objects.create(parent_transaction=instance, paid_for=debtor, value=share)

        self._save_receipts(instance)

        handle_message(ParentTransactionCreated(context_data={"parent_transaction": instance, "room": instance.room}))

        return instance

    def _save_receipts(self, parent_transaction: ParentTransaction):
        receipt_files = self.cleaned_data.get("receipts") or []
        if not receipt_files:
            return

        for uploaded_file in receipt_files:
            Receipt.objects.create(
                parent_transaction=parent_transaction,
                file=uploaded_file,
                original_name=uploaded_file.name,
                content_type=uploaded_file.content_type,
                size=uploaded_file.size,
                uploaded_by=getattr(self._request, "user", None),
            )

    def _build_category_queryset(self):
        if self._room:
            return RoomCategoryService(room=self._room).get_category_queryset()
        return Category.objects.order_by("order_index", "id")
