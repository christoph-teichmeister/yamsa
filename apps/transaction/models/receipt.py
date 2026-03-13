import os
import uuid

from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _lazy

from apps.account.models import User


def receipt_upload_path(instance, filename):
    room_id = instance.parent_transaction.room_id

    base_name, extension = os.path.splitext(os.path.basename(filename))
    safe_name = slugify(base_name) or "file"
    extension = extension.lstrip(".")
    unique_id = uuid.uuid4().hex
    final_name = f"{unique_id}.{safe_name}.{extension}" if extension else f"{unique_id}.{safe_name}"

    return os.path.join("receipts", str(room_id), final_name)


class Receipt(CommonInfo):
    parent_transaction = models.ForeignKey(
        "ParentTransaction",
        related_name="receipts",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to=receipt_upload_path)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    uploaded_by = models.ForeignKey(
        User,
        related_name="uploaded_receipts",
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = _lazy("Transaction receipt")
        verbose_name_plural = _lazy("Transaction receipts")

    def __str__(self) -> str:
        return self.original_name
