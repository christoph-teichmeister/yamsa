from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionDetailView(TransactionBaseContext, generic.DetailView):
    model = ParentTransaction
    context_object_name = "parent_transaction"
    template_name = "transaction/detail.html"

    @context
    @cached_property
    def child_transactions(self):
        return self.object.child_transactions.all()
