from ai_django_core.models import CommonInfo
from django.db import models


class Transaction(CommonInfo):
    description = models.TextField(max_length=500)
    paid_for = models.ForeignKey(
        "account.User", related_name="owes_transactions", on_delete=models.CASCADE
    )
    paid_by = models.ForeignKey(
        "account.User", related_name="made_transactions", on_delete=models.CASCADE
    )

    room = models.ForeignKey(
        "room.Room",
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    value = models.DecimalField(decimal_places=2, max_digits=10)

    settled = models.BooleanField(default=False)
    settled_at = models.DateField(blank=True, null=True)

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transaction"

    def __str__(self):
        return f"{self.paid_by} paid {self.value}€ for {self.paid_for}"
