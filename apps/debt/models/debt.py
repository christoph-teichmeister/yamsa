from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.debt.managers import DebtManager
from apps.debt.querysets import DebtQuerySet


class Debt(FullCleanOnSaveMixin, CommonInfo, models.Model):
    debitor = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="debts")
    creditor = models.ForeignKey("account.User", on_delete=models.CASCADE, related_name="debts_to_be_settled")
    room = models.ForeignKey("room.Room", on_delete=models.CASCADE, related_name="debts")

    value = models.DecimalField(decimal_places=2, max_digits=10)

    currency = models.ForeignKey("currency.Currency", related_name="debts", on_delete=models.DO_NOTHING)

    settled = models.BooleanField(default=False)
    settled_at = models.DateField(blank=True, null=True)

    objects = DebtManager.from_queryset(DebtQuerySet)()

    class Meta:
        verbose_name = "Debt"
        verbose_name_plural = "Debts"

    def __str__(self):
        return (
            f"{'Settled: ' if self.settled else ''}{self.debitor.name} "
            f"owes {self.value}{self.currency.sign} to {self.creditor.name}"
        )
