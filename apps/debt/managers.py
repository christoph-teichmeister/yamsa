from django.db.models import Manager, QuerySet

from apps.core.utils import add_or_update_dict
from apps.debt.querysets import NewDebtQuerySet


class NewDebtManager(Manager):
    def get_queryset(self) -> NewDebtQuerySet:
        return NewDebtQuerySet(self.model, using=self._db)
