import mimetypes
from decimal import Decimal

from django import forms
from django.contrib.postgres.forms import SimpleArrayField
from django.core.files.uploadedfile import UploadedFile
from django.db.models import QuerySet
from django.http import HttpRequest

from apps.account.models import User
from apps.room.models import Room
from apps.transaction.forms.mixins.room_category_field import RoomCategoryFieldMixin
from apps.transaction.forms.mixins.split_shares import SplitSharesMixin
from apps.transaction.models import ChildTransaction, ParentTransaction, Receipt
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


class TransactionCreateForm(SplitSharesMixin, RoomCategoryFieldMixin, forms.ModelForm):
    total_value = forms.DecimalField(decimal_places=2, max_digits=10)
    # The total the currently submitted `value` row values were last computed against - carried
    # in a hidden field because, unlike the edit form, there is no persisted split to compare to.
    reference_total_value = forms.DecimalField(decimal_places=2, max_digits=10, required=False)

    # Per-row ChildTransaction fields, parallel arrays like TransactionEditForm's.
    paid_for = SimpleArrayField(forms.IntegerField())
    value = SimpleArrayField(forms.DecimalField(decimal_places=2, max_digits=10))

    room_slug = forms.CharField()
    category = RoomCategoryFieldMixin.build_category_field()
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

    def __init__(
        self, *args: object, request: HttpRequest | None = None, room: Room | None = None, **kwargs: object
    ) -> None:
        self._request = request
        self._room = room
        super().__init__(*args, **kwargs)
        self.narrow_category_field_to(room)

    def _share_room_users(self) -> QuerySet:
        return User.objects.filter(room=self._room)

    def clean(self) -> dict:
        cleaned_data = super().clean()
        total_value = cleaned_data.get("total_value")
        paid_for = cleaned_data.get("paid_for")
        values = cleaned_data.get("value")

        if total_value is None or not paid_for or values is None:
            return cleaned_data
        if not self.shares_have_equal_length(paid_for, values):
            return cleaned_data

        reference_total_value = cleaned_data.get("reference_total_value") or Decimal("0.00")
        if total_value != reference_total_value:
            values = split_total_across_paid_for(total_value, paid_for)

        if not self.share_amounts_are_valid(values):
            return cleaned_data

        # A zero share is no debt; the edit form drops it the same way.
        shares = [(debtor, value) for debtor, value in zip(paid_for, values, strict=True) if value != 0]
        cleaned_data["paid_for"] = [debtor for debtor, _ in shares]
        cleaned_data["value"] = [value for _, value in shares]
        cleaned_data["total_value"] = sum(cleaned_data["value"], Decimal("0.00"))
        return cleaned_data

    def clean_receipts(self) -> list:
        uploaded_files = self.files.getlist(self.add_prefix("receipts"))
        errors = []
        for uploaded_file in uploaded_files:
            uploaded_file.content_type = (
                getattr(uploaded_file, "content_type", None)
                or mimetypes.guess_type(uploaded_file.name)[0]
                or "application/octet-stream"
            )
            errors += self._receipt_errors(uploaded_file)

        if errors:
            raise forms.ValidationError(errors)

        if uploaded_files:
            uploader = getattr(self._request, "user", None)
            if not uploader or not uploader.is_authenticated:
                raise forms.ValidationError(
                    RECEIPT_AUTH_REQUIRED_MESSAGE,
                    code="authentication_required",
                )

        return uploaded_files

    @staticmethod
    def _receipt_errors(uploaded_file: UploadedFile) -> list[forms.ValidationError]:
        errors = []
        if uploaded_file.content_type not in RECEIPT_ACCEPTED_CONTENT_TYPES:
            errors.append(
                forms.ValidationError(
                    "Receipts must be PDF or an image (PNG, JPEG, WebP, GIF).",
                    code="invalid_content_type",
                )
            )
        if uploaded_file.size > MAX_RECEIPT_SIZE:
            errors.append(forms.ValidationError("Each receipt must be 5 MB or smaller.", code="file_too_large"))
        return errors

    def save(self, commit: bool = True) -> ParentTransaction:
        instance: ParentTransaction = super().save(commit)

        paid_for_entries = self.cleaned_data["paid_for"]
        values = self.cleaned_data["value"]
        for debtor_id, share in zip(paid_for_entries, values, strict=True):
            ChildTransaction.objects.create(parent_transaction=instance, paid_for_id=debtor_id, value=share)

        self._save_receipts(instance)

        return instance

    def _save_receipts(self, parent_transaction: ParentTransaction) -> None:
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
