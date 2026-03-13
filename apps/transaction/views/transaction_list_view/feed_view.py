from collections.abc import MutableMapping

from django.views import generic

from apps.transaction.views.transaction_list_view.mixin import TransactionFeedMixin


class TransactionFeedView(TransactionFeedMixin, generic.TemplateView):
    template_name = "transaction/partials/_transaction_batch.html"

    def get_context_data(self, **kwargs: object) -> MutableMapping[str, object]:
        context = super().get_context_data(**kwargs)
        context.update(self.build_feed_context(initial_render=False))
        return context
