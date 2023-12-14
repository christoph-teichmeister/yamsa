from django.views import generic

from apps.transaction.models import ParentTransaction


class TransactionListHTMXView(generic.ListView):
    model = ParentTransaction
    context_object_name = "parent_transactions"
    template_name = "transaction/_list.html"

    def get_queryset(self):
        return self.model.objects.filter(room=self.request.room)
