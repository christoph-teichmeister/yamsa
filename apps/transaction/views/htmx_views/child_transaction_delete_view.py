from django.views import generic

from apps.core import htmx
from apps.transaction.models import ChildTransaction


class ChildTransactionDeleteHTMXView(htmx.FormHtmxResponseMixin, generic.DeleteView):
    model = ChildTransaction

    hx_trigger = "reloadTransactionEditView"
    toast_success_message = "Transaction successfully deleted!"
    toast_error_message = "There was an error deleting the transaction"
