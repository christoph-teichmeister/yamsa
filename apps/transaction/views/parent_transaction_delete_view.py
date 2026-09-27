from django.urls import reverse
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.views.mixins import RoomNotClosedRequiredMixin
from apps.transaction.messages.events.transaction import ParentTransactionDeleted
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class ParentTransactionDeleteView(RoomNotClosedRequiredMixin, TransactionBaseContext, generic.DeleteView):
    model = ParentTransaction
    template_name = "transaction/edit.html"

    def get_success_url(self):
        return reverse(
            viewname="transaction:list",
            kwargs={"room_slug": self.request.room.slug},
        )

    def form_valid(self, form):
        room_id = self.object.room_id

        # Sent while the shares still exist: the news entry and the push notifications read the
        # amount and the debtors from them.
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

        # The recalculation the event triggered still counted the shares, so it has to run again
        # now that they are gone.
        DebtOptimiseService.process(room_id=room_id)

        return form_valid_return
