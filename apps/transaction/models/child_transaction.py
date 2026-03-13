from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from apps.core.models.mixins import FullCleanOnSaveMixin


class ChildTransaction(FullCleanOnSaveMixin, CommonInfo):
    parent_transaction = models.ForeignKey("ParentTransaction", on_delete=models.CASCADE)

    paid_for = models.ForeignKey("account.User", related_name="owes_child_transactions", on_delete=models.CASCADE)
    value = models.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        ordering = ("-id",)
        default_related_name = "child_transactions"
        verbose_name = _lazy("Child Transaction")
        verbose_name_plural = _lazy("Child Transactions")

    def __str__(self) -> str:
        return _("{paid_by} paid {value}{currency} for {paid_for}").format(
            paid_by=self.parent_transaction.paid_by,
            value=self.value,
            currency=self.parent_transaction.currency.sign,
            paid_for=self.paid_for,
        )
