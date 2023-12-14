from django.views import generic
from django_context_decorator import context
from functools import cached_property

from apps.transaction.forms.transaction_create_form import TransactionCreateForm
from apps.transaction.models import ParentTransaction
from apps.core import htmx


class TransactionCreateView(htmx.FormHtmxResponseMixin, generic.CreateView):
    model = ParentTransaction
    form_class = TransactionCreateForm
    template_name = "transaction/create.html"

    hx_trigger = "loadTransactionList"
    toast_success_message = "Transaction created successfully!"
    toast_error_message = "There was an error creating the Transaction"

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "transaction")
