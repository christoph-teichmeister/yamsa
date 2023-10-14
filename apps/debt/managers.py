from django.db.models import Manager

from apps.debt.querysets import NewDebtQuerySet


class NewDebtManager(Manager):
    def get_queryset(self) -> NewDebtQuerySet:
        return NewDebtQuerySet(self.model, using=self._db)
