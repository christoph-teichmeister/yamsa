from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.transaction.messages.events.transaction import ParentTransactionDeleted
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ParentTransactionDeleteView(TransactionBaseContext, generic.DeleteView):
    model = ParentTransaction
    template_name = "transaction/edit.html"

    def get_success_url(self):
        return reverse(
            viewname="transaction:list",
            kwargs={"room_slug": self.request.room.slug},
        )

    def form_valid(self, form):
        handle_message(
            ParentTransactionDeleted(
                context_data={
                    "parent_transaction": self.object,
                    "room": self.object.room,
                    "user_who_deleted": self.request.user,
                }
            )
        )

        self.object.child_transactions.all().delete()
        form_valid_return = super().form_valid(form)

        return form_valid_return
