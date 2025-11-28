import os
import uuid

from ambient_toolbox.models import CommonInfo
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.text import slugify
from django.utils.timezone import now
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from apps.account.models import User
from apps.core.models.mixins import FullCleanOnSaveMixin

DEFAULT_CATEGORY_SLUG = "misc"
DEFAULT_CATEGORY_PK = 10  # Matches the seeded "misc" category (last of the ten defaults)


class Category(FullCleanOnSaveMixin, CommonInfo):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10)
    color = models.CharField(max_length=7, blank=True, null=True)
    order_index = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("order_index", "id")
        verbose_name = _lazy("Transaction Category")
        verbose_name_plural = _lazy("Transaction Categories")

    def __str__(self) -> str:
        return f"{self.emoji} {self.name}"

    @classmethod
    def get_default_category(cls):
        default = cls.objects.filter(slug=DEFAULT_CATEGORY_SLUG).first()
        if default:
            return default
        return cls.objects.filter(is_default=True).order_by("order_index").first()


class ParentTransaction(FullCleanOnSaveMixin, CommonInfo):
    description = models.TextField(max_length=50)
    further_notes = models.TextField(max_length=5000, blank=True, null=True)

    paid_by = models.ForeignKey("account.User", related_name="made_parent_transactions", on_delete=models.CASCADE)
    paid_at = models.DateTimeField(_lazy("Paid at"), default=now, db_index=True)

    room = models.ForeignKey("room.Room", on_delete=models.CASCADE, related_name="parent_transactions")

    currency = models.ForeignKey("currency.Currency", related_name="parent_transactions", on_delete=models.DO_NOTHING)
    category = models.ForeignKey(
        "Category",
        related_name="transactions",
        on_delete=models.PROTECT,
        default=DEFAULT_CATEGORY_PK,
    )

    class Meta:
        ordering = ("-id",)
        default_related_name = "parent_transactions"
        verbose_name = _lazy("Parent Transaction")
        verbose_name_plural = _lazy("Parent Transactions")

    def __str__(self) -> str:
        return f"{self.id}: {self.description}"

    @property
    def value(self):
        return self.child_transactions.aggregate(Sum("value"))["value__sum"]

    def save(self, *args, **kwargs):
        if not getattr(self, "category_id", None):
            default_category = Category.get_default_category()
            if default_category:
                self.category = default_category
        super().save(*args, **kwargs)


class ChildTransaction(FullCleanOnSaveMixin, CommonInfo):
    parent_transaction = models.ForeignKey("ParentTransaction", on_delete=models.CASCADE)

    paid_for = models.ForeignKey("account.User", related_name="owes_child_transactions", on_delete=models.CASCADE)
    value = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        ordering = ("-id",)
        default_related_name = "child_transactions"
        verbose_name = _lazy("Child Transaction")
        verbose_name_plural = _lazy("Child Transactions")

    def __str__(self) -> str:
        return _("{paid_by} paid {value}{currency} for {paid_for}").format(
            paid_by=self.parent_transaction.paid_by,
            value=self.value,
            currency=self.parent_transaction.currency.sign,
            paid_for=self.paid_for,
        )


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
