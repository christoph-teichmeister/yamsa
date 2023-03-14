from ai_django_core.models import CommonInfo
from django.db import models


class Transaction(CommonInfo):
    description = models.TextField(max_length=500)
    paid_for = models.ManyToManyField(
        "account.User",
        through="transaction.UserConnectionToTransaction",
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
        ordering = ("-id",)
        verbose_name = "Transaction"
        verbose_name_plural = "Transaction"

    def __str__(self):
        return f"{self.paid_by} paid {self.value}€ for {', '.join(self.paid_for.values_list('name', flat=True))}"


class UserConnectionToTransaction(models.Model):
    user = models.ForeignKey(
        "account.User", on_delete=models.CASCADE, related_name="owes_transactions"
    )
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "User-Connection to Transaction"
        verbose_name_plural = "User-Connections to Transactions"

    def __str__(self):
        return (
            f"{self.user} owes {self.transaction.value} to {self.transaction.paid_by}"
        )
