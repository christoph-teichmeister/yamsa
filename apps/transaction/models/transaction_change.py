from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _lazy


class TransactionChange(models.Model):
    """One entry of a transaction's history: its creation, an edit, or a receipt added or removed.

    Written by the views that perform the action, never by a form's save(). Names and values are
    stored as they were at that moment, so a later rename or edit cannot rewrite the history.
    """

    class Kind(models.TextChoices):
        CREATED = "created", _lazy("Created")
        EDITED = "edited", _lazy("Edited")
        RECEIPT_ADDED = "receipt_added", _lazy("Receipt added")
        RECEIPT_REMOVED = "receipt_removed", _lazy("Receipt removed")

    parent_transaction = models.ForeignKey("ParentTransaction", related_name="changes", on_delete=models.CASCADE)
    # Nullable so deleting an account does not take the room's history with it.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="transaction_changes", null=True, on_delete=models.SET_NULL
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    # The receipt's file name for receipt entries.
    detail = models.CharField(max_length=255, blank=True)
    # Field-level diffs of an edit: {"field", "old", "new"}, plus "who" and "sign" where they apply.
    changes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = _lazy("Transaction change")
        verbose_name_plural = _lazy("Transaction changes")

    def __str__(self) -> str:
        return f"{self.parent_transaction_id}: {self.kind}"
