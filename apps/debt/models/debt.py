from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

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
        verbose_name = _lazy("Debt")
        verbose_name_plural = _lazy("Debts")

    def __str__(self):
        debitor = self.debitor.name
        creditor = self.creditor.name
        value = self.value
        currency = self.currency.sign
        if self.settled:
            full_sentence = _("Settled: {debitor} owes {value}{currency} to {creditor}")
        else:
            full_sentence = _("{debitor} owes {value}{currency} to {creditor}")
        return full_sentence.format(
            debitor=debitor,
            value=value,
            currency=currency,
            creditor=creditor,
        )
