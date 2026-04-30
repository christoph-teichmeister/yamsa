from django.views import generic

from apps.transaction.views.transaction_list_view.mixin import TransactionFeedMixin


class TransactionListView(TransactionFeedMixin, generic.TemplateView):
    template_name = "transaction/list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        total_count = self.get_base_queryset().count()
        context["transactions_available"] = total_count > 0
        context["transactions_total_count"] = total_count
        context["transaction_search_query"] = self.get_search_query()
        return context
