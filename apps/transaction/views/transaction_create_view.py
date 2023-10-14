from django.views import generic

from apps.transaction.forms import TransactionCreateForm
from apps.transaction.models import ParentTransaction
from apps.core import htmx


class TransactionCreateView(htmx.FormHtmxResponseMixin, generic.CreateView):
    model = ParentTransaction
    form_class = TransactionCreateForm
    template_name = "room/detail.html"

    hx_trigger = "reloadTransactionList"
    toast_success_message = "Transaction created successfully"
