from django.db import transaction
from django.db.models import QuerySet
from django.forms import BaseForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin
from apps.transaction.messages.events.transaction import ChildTransactionDeleted, ParentTransactionDeleted
from apps.transaction.models import ChildTransaction, ParentTransaction
from apps.transaction.utils import split_amount_exact
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ChildTransactionDeleteView(
    RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, TransactionBaseContext, generic.DeleteView
):
    model = ChildTransaction
    template_name = "transaction/edit.html"

    _removed_last_share = False

    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(parent_transaction__room=self.request.room)

    def get_success_url(self) -> str:
        # Decided in form_valid(), where the share count is read under the parent's lock.
        if self._removed_last_share:
            return reverse(
                viewname="transaction:list",
                kwargs={"room_slug": self.request.room.slug},
            )

        return reverse(
            viewname="transaction:edit",
            kwargs={"pk": self.object.parent_transaction_id, "room_slug": self.request.room.slug},
        )

    def form_valid(self, form: BaseForm) -> HttpResponse:
        deleted = None
        # The parent row is locked so that two concurrent removals cannot both see "another share
        # remains" and leave a transaction without shares behind.
        with transaction.atomic():
            parent_transaction = ParentTransaction.objects.select_for_update().get(pk=self.object.parent_transaction_id)
            self._removed_last_share = not parent_transaction.child_transactions.exclude(pk=self.object.pk).exists()
            if self._removed_last_share:
                # Taken while this share still exists: it is part of what the transaction carried.
                deleted = ParentTransactionDeleted.context_before_deletion(
                    parent_transaction, user_who_deleted=self.request.user
                )
                parent_transaction.delete()
            else:
                self._hand_value_to_remaining_shares()
                self.object.delete()
                # The share is gone the moment it is removed, not when the edit form is saved; a visitor
                # who leaves the form here must not find the debt it carried still standing. Stamping the
                # remover as the last modifier is what the event's notification names as the editor.
                parent_transaction.save(update_fields=("lastmodified_at", "lastmodified_by"))

        if deleted is not None:
            handle_message(ParentTransactionDeleted(context_data=deleted))
        else:
            handle_message(
                ChildTransactionDeleted(
                    context_data={"parent_transaction": parent_transaction, "room": parent_transaction.room}
                )
            )

        return HttpResponseRedirect(self.get_success_url())

    def _hand_value_to_remaining_shares(self) -> None:
        # The transaction total is the sum of its shares, so a removed share would silently lower it.
        remaining = list(self.object.parent_transaction.child_transactions.exclude(pk=self.object.pk))
        if not remaining:
            return
        for share, extra in zip(remaining, split_amount_exact(self.object.value, len(remaining)), strict=True):
            share.value += extra
        ChildTransaction.objects.bulk_update(remaining, fields=("value",))
