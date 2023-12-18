from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionDeleted
from apps.transaction.models import ChildTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ChildTransactionDeleteView(TransactionBaseContext, generic.DeleteView):
    model = ChildTransaction
    template_name = "transaction/edit.html"

    def get_success_url(self):
        # If the count is 1, then that means that we are currently deleting the last child_transaction,
        # so the parent_transaction _will_ have no child_transactions anymore, after this operation is executed
        if self.object.parent_transaction.child_transactions.count() == 1:
            return reverse(
                viewname="transaction-list",
                kwargs={"room_slug": self.request.room.slug},
            )

        return reverse(
            viewname="transaction-edit",
            kwargs={"pk": self.object.parent_transaction.id, "room_slug": self.request.room.slug},
        )

    def form_valid(self, form):
        form_valid_return = super().form_valid(form)
        parent_transaction = self.object.parent_transaction

        if parent_transaction.child_transactions.count() == 0:
            handle_message(
                ParentTransactionDeleted(
                    context_data={
                        "parent_transaction": parent_transaction,
                        "room": self.object.parent_transaction.room,
                    }
                )
            )

            parent_transaction.delete()

        # There is no need to send a notification, when a child_transaction has been deleted, as this can only be
        # done when editing a transaction anyway - a user would have to save the form afterward, which will trigger
        # a ParentTransactionUpdated event, which notifies everyone

        return form_valid_return
