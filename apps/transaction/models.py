from _decimal import Decimal

from ai_django_core.models import CommonInfo
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils import timezone


class Transaction(CommonInfo):
    description = models.TextField(max_length=500)
    paid_for = models.ManyToManyField(
        "account.User",
        through="debt.Debt",
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
        multiple_people = self.paid_for.all().count() > 1
        return (
            f"{self.paid_by} paid {self.value}€ for {'each: ' if multiple_people else ''}"
            f"{', '.join(self.paid_for.values_list('name', flat=True))}"
        )

    def save(self, *args, **kwargs):
        # Set settled_at if settled is True and settled_at was not already set (Meaning, the transaction was just
        # settled)
        if self.settled and not self.settled_at:
            self.settled_at = timezone.now()

        # Clear settled_at if it was set AND the transaction is not marked as settled (Meaning, for whatever reason,
        # the transaction was just marked as not settled, although it was marked as such before)
        if not self.settled and self.settled_at:
            self.settled_at = None

        super().save(*args, **kwargs)


@receiver(m2m_changed, sender=Transaction.paid_for.through)
def transaction_paid_for(sender, **kwargs):
    action = kwargs.pop("action", None)
    pk_set = kwargs.pop("pk_set", None)
    instance: Transaction = kwargs.pop("instance", None)

    if action == "post_add":
        instance.value = round(Decimal(instance.value / len(pk_set)), 2)
        instance.save()

        # Mark any debts created because of this transaction, which belong to the debitor as settled, as a debitor
        # can not owe themself money
        instance.paid_by.owes_transactions.filter(
            user=instance.paid_by, transaction_id=instance.id
        ).update(settled=True, settled_at=timezone.now())

        from apps.moneyflow.models import MoneyFlow

        MoneyFlow.objects.create_or_update_flows_for_transaction(transaction=instance)
