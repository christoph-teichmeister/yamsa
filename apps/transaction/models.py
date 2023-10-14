from ambient_toolbox.models import CommonInfo
from django.db import models
from django.db.models.aggregates import Sum


class ParentTransaction(CommonInfo):
    description = models.TextField(max_length=500)
    paid_by = models.ForeignKey("account.User", related_name="made_parent_transactions", on_delete=models.CASCADE)

    room = models.ForeignKey("room.Room", on_delete=models.CASCADE, related_name="parent_transactions")

    currency = models.ForeignKey("currency.Currency", related_name="parent_transactions", on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ("-id",)
        default_related_name = "parent_transactions"
        verbose_name = "Parent Transaction"
        verbose_name_plural = "Parent Transactions"

    def __str__(self):
        return f"{self.id}: {self.paid_by.name} paid {self.value}{self.currency.sign}"

    @property
    def value(self):
        return self.child_transactions.aggregate(Sum("value"))["value__sum"]


class ChildTransaction(CommonInfo):
    parent_transaction = models.ForeignKey("ParentTransaction", on_delete=models.CASCADE)

    paid_for = models.ForeignKey("account.User", related_name="owes_child_transactions", on_delete=models.CASCADE)
    value = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        ordering = ("-id",)
        default_related_name = "child_transactions"
        verbose_name = "Child Transaction"
        verbose_name_plural = "Child Transactions"

    def __str__(self):
        return (
            f"{self.parent_transaction.paid_by} paid {self.value}{self.parent_transaction.currency.sign} for"
            f" {self.paid_for}"
        )
