from functools import cached_property

from django.views import generic
from django_context_decorator import context

from apps.transaction.models import ParentTransaction


class TransactionListView(generic.ListView):
    model = ParentTransaction
    context_object_name = "parent_transactions"
    template_name = "transaction/list.html"

    def get_queryset(self):
        return self.model.objects.filter(room=self.request.room)

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "transaction")
