from django.views import generic

from apps.currency.models import Currency
from apps.transaction.models import Category
from apps.transaction.views.transaction_list_view.mixin import TransactionFeedMixin


class TransactionListView(TransactionFeedMixin, generic.TemplateView):
    template_name = "transaction/list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        base_queryset = self.get_base_queryset()
        total_count = base_queryset.count()
        context["transactions_available"] = total_count > 0
        context["transactions_total_count"] = total_count
        context["latest_transaction"] = base_queryset.first()
        context["transaction_search_query"] = self.get_search_query()
        context.update(self._build_filter_context())
        return context

    def _build_filter_context(self) -> dict[str, object]:
        category_slug = self.get_category_slug()
        currency_code = self.get_currency_code()

        # Category rows are global, so an unscoped slug lookup would render another room's category
        # name in this room's chip. Scoped by transactions rather than by RoomCategory: the filter
        # only ever comes from a breakdown legend entry, and that lists exactly the categories this
        # room has spent on - a room that never opened the category manager has no RoomCategory rows.
        category = (
            Category.objects.filter(slug=category_slug, transactions__room=self.request.room).distinct().first()
            if category_slug
            else None
        )
        currency = Currency.objects.filter(code__iexact=currency_code).first() if currency_code else None

        return {
            "transaction_category_filter": category_slug,
            "transaction_currency_filter": currency_code,
            # Fall back to the raw values so an unknown slug/code is still visible in the chip
            # instead of showing an unexplained empty list.
            "transaction_filter_category_label": str(category) if category else category_slug,
            "transaction_filter_currency_label": currency.code if currency else currency_code,
            "transaction_filter_active": bool(category_slug or currency_code),
        }
