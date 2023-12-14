from django.db.models import Manager

from apps.debt.querysets import DebtQuerySet


class DebtManager(Manager):
    def get_queryset(self) -> DebtQuerySet:
        return DebtQuerySet(self.model, using=self._db)
