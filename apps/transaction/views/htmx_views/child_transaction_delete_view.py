from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.core import htmx
from apps.transaction.models import ChildTransaction


class ChildTransactionDeleteHTMXView(htmx.FormHtmxResponseMixin, generic.DeleteView):
    model = ChildTransaction

    hx_trigger = "reloadTransactionEditView"
    toast_success_message = "Transaction successfully deleted!"
    toast_error_message = "There was an error deleting the transaction"

    def get_response(self):
        # TODO CT: Nope, this does not work
        return HttpResponseRedirect(
            redirect_to=reverse(viewname="room-detail", kwargs={"slug": self.object.parent_transaction.room.slug})
        )

    def form_valid(self, form):
        form_valid_return = super().form_valid(form)

        parent_transactions_still_has_child_transactions = self.object.parent_transaction.child_transactions.count() > 0
        if not parent_transactions_still_has_child_transactions:
            self.object.parent_transaction.delete()

        return form_valid_return
