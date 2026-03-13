from decimal import Decimal

from ambient_toolbox.models import CommonInfo
from django.db import models
from django.db.models.aggregates import Sum
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _lazy

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.transaction.models.constants import resolve_default_category_pk


class ParentTransaction(FullCleanOnSaveMixin, CommonInfo):
    description = models.TextField(max_length=50)
    further_notes = models.TextField(max_length=5000, blank=True, null=True)

    paid_by = models.ForeignKey("account.User", related_name="made_parent_transactions", on_delete=models.CASCADE)
    paid_at = models.DateTimeField(_lazy("Paid at"), default=now, db_index=True)

    room = models.ForeignKey("room.Room", on_delete=models.CASCADE, related_name="parent_transactions")

    currency = models.ForeignKey(
        "currency.Currency",
        related_name="parent_transactions",
        on_delete=models.PROTECT,
    )
    category = models.ForeignKey(
        "Category",
        related_name="transactions",
        on_delete=models.PROTECT,
        default=resolve_default_category_pk,
    )

    class Meta:
        ordering = ("-id",)
        default_related_name = "parent_transactions"
        verbose_name = _lazy("Parent Transaction")
        verbose_name_plural = _lazy("Parent Transactions")

    def __str__(self) -> str:
        return f"{self.id}: {self.description}"

    @property
    def value(self) -> Decimal:
        aggregate = self.child_transactions.aggregate(Sum("value"))
        total = aggregate["value__sum"]
        if total is None:
            return Decimal("0")
        return total

    def save(self, *args, **kwargs):
        if not getattr(self, "category_id", None) and getattr(self, "room", None):
            from apps.transaction.services.room_category_service import RoomCategoryService

            default_category = RoomCategoryService(room=self.room).get_default_category()
            if default_category:
                self.category = default_category
        super().save(*args, **kwargs)
