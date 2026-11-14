from django.db import models


class LiveManager(models.Manager):
    """Skips rows whose transaction is in its undo window, so every list, sum and export ignores them.

    Works for the transaction itself and for its shares. The lookup is derived from the model
    rather than passed in: a related manager is built from this class without the constructor
    arguments, so the model is the only thing it is sure to have.
    """

    def get_queryset(self) -> models.QuerySet:
        has_own_flag = any(field.name == "deleted_at" for field in self.model._meta.get_fields())
        lookup = "deleted_at" if has_own_flag else "parent_transaction__deleted_at"
        return super().get_queryset().filter(**{f"{lookup}__isnull": True})
