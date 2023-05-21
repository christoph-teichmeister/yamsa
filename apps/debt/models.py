from django.db import models
from django.utils import timezone

from apps.debt.managers import DebtManager


class Debt(models.Model):
    user = models.ForeignKey(
        "account.User", on_delete=models.CASCADE, related_name="owes_transactions"
    )
    transaction = models.ForeignKey("transaction.Transaction", on_delete=models.CASCADE)

    settled = models.BooleanField(default=False)
    settled_at = models.DateField(blank=True, null=True)

    objects = DebtManager()

    class Meta:
        verbose_name = "Debt"
        verbose_name_plural = "Debts"

    def __str__(self):
        return (
            f"{self.user} owes {self.transaction.value} to {self.transaction.paid_by}"
        )

    def save(self, *args, **kwargs):
        if self.user_id == self.transaction.paid_by_id:
            self.settled = True

        # Set settled_at if settled is True and settled_at was not already set (Meaning, the transaction was just
        # settled)
        if self.settled and not self.settled_at:
            self.settled_at = timezone.now()

        # Clear settled_at if it was set AND the transaction is not marked as settled (Meaning, for whatever reason,
        # the transaction was just marked as not settled, although it was marked as such before)
        if not self.settled and self.settled_at:
            self.settled_at = None

        super().save(*args, **kwargs)
