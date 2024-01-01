from django.db.models import Sum
from django.views import generic

from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionListView(TransactionBaseContext, generic.ListView):
    model = ParentTransaction
    context_object_name = "parent_transactions"
    template_name = "transaction/list.html"

    def get_queryset(self):
        return (
            self.model.objects.filter(room=self.request.room)
            .select_related("paid_by", "currency")
            .prefetch_related("child_transactions")
            .annotate(total_child_value=Sum("child_transactions__value"))
        )
