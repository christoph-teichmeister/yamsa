from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils import timezone
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
    # The debitor says they paid, the creditor has not confirmed yet. Still unsettled for every balance and
    # optimisation purpose; only `settle()` makes the money count as moved.
    awaiting_confirmation = models.BooleanField(default=False)

    objects = DebtManager.from_queryset(DebtQuerySet)()

    class Meta:
        verbose_name = _lazy("Debt")
        verbose_name_plural = _lazy("Debts")
        indexes = (models.Index(fields=("room", "settled"), name="debt_room_settled_idx"),)
        constraints = (
            models.CheckConstraint(
                condition=~models.Q(settled=True, awaiting_confirmation=True),
                name="debt_settled_not_awaiting_confirmation",
            ),
        )

    def __str__(self) -> str:
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

    # The transitions below only persist state. Locking and notifications belong to the calling view; each returns
    # whether anything changed so a repeated request stays silent.

    def mark_as_paid(self) -> bool:
        """Debitor side: open -> awaiting confirmation."""
        if self.settled or self.awaiting_confirmation:
            return False
        self.awaiting_confirmation = True
        self.save()
        return True

    def settle(self) -> bool:
        """Creditor side: open or awaiting confirmation -> settled. One-way."""
        if self.settled:
            return False
        self.settled = True
        self.awaiting_confirmation = False
        self.settled_at = timezone.localdate()
        self.save()
        return True

    def reopen(self) -> bool:
        """Awaiting confirmation -> open, when the creditor rejects or the debitor withdraws."""
        if self.settled or not self.awaiting_confirmation:
            return False
        self.awaiting_confirmation = False
        self.save()
        return True
