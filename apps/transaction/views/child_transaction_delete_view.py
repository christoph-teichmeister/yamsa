from django.http import HttpResponse
from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.room.views.mixins import RoomNotClosedRequiredMixin
from apps.transaction.messages.events.transaction import ChildTransactionDeleted, ParentTransactionDeleted
from apps.transaction.models import ChildTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ChildTransactionDeleteView(RoomNotClosedRequiredMixin, TransactionBaseContext, generic.DeleteView):
    model = ChildTransaction
    template_name = "transaction/edit.html"

    def get_success_url(self) -> str:
        # If the count is 1, then that means that we are currently deleting the last child_transaction,
        # so the parent_transaction _will_ have no child_transactions anymore, after this operation is executed
        if self.object.parent_transaction.child_transactions.count() == 1:
            return reverse(
                viewname="transaction:list",
                kwargs={"room_slug": self.request.room.slug},
            )

        return reverse(
            viewname="transaction:edit",
            kwargs={"pk": self.object.parent_transaction.id, "room_slug": self.request.room.slug},
        )

    def form_valid(self, form) -> HttpResponse:
        parent_transaction = self.object.parent_transaction
        # Taken while this share still exists: it is part of what the transaction carried.
        deleted = (
            ParentTransactionDeleted.context_before_deletion(parent_transaction, user_who_deleted=self.request.user)
            if parent_transaction.child_transactions.count() == 1
            else None
        )

        form_valid_return = super().form_valid(form)

        if deleted is not None:
            parent_transaction.delete()
            handle_message(ParentTransactionDeleted(context_data=deleted))
        else:
            # The share is gone the moment it is removed, not when the edit form is saved; a visitor
            # who leaves the form here must not find the debt it carried still standing. Stamping the
            # remover as the last modifier is what the event's notification names as the editor.
            parent_transaction.save(update_fields=("lastmodified_at", "lastmodified_by"))
            handle_message(
                ChildTransactionDeleted(
                    context_data={"parent_transaction": parent_transaction, "room": parent_transaction.room}
                )
            )

        return form_valid_return
