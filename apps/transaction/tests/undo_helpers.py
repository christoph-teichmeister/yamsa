from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.room.models import Room
from apps.transaction.models import ParentTransaction
from apps.transaction.services.transaction_deletion_service import UNDO_WINDOW


def delete_url(room: Room, parent: ParentTransaction) -> str:
    return reverse("transaction:parent-transaction-delete", kwargs={"room_slug": room.slug, "pk": parent.pk})


def restore_url(room: Room, parent: ParentTransaction) -> str:
    return reverse("transaction:parent-transaction-restore", kwargs={"room_slug": room.slug, "pk": parent.pk})


def let_window_pass(parent: ParentTransaction) -> None:
    ParentTransaction.all_objects.filter(pk=parent.pk).update(
        deleted_at=timezone.now() - UNDO_WINDOW - timedelta(seconds=1)
    )
