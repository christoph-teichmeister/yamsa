from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils import timezone


class Transaction(CommonInfo):
    description = models.TextField(max_length=500)
    paid_for = models.ManyToManyField("account.User")
    paid_by = models.ForeignKey("account.User", related_name="made_transactions", on_delete=models.CASCADE)

    room = models.ForeignKey(
        "room.Room",
        on_delete=models.CASCADE,
        related_name="transactions",
    )

    value = models.DecimalField(decimal_places=2, max_digits=10)

    currency = models.ForeignKey("currency.Currency", related_name="transactions", on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ("-id",)
        verbose_name = "Transaction"
        verbose_name_plural = "Transaction"

    def __str__(self):
        multiple_people = self.paid_for.all().count() > 1
        return (
            f"{self.paid_by} paid {self.value}{self.currency.sign} for {'each: ' if multiple_people else ''}"
            f"{', '.join(self.paid_for.values_list('name', flat=True))}"
        )
