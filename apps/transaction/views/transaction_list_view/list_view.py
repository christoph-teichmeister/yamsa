from django.views import generic

from apps.transaction.views.transaction_list_view.mixin import TransactionFeedMixin


class TransactionListView(TransactionFeedMixin, generic.TemplateView):
    template_name = "transaction/list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        base_queryset = self.get_base_queryset()
        total_count = base_queryset.count()
        context["transactions_available"] = total_count > 0
        context["transactions_total_count"] = total_count
        context.update(self.build_feed_context(initial_render=True, queryset=base_queryset))
        return context
