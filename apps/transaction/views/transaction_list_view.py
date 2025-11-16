from datetime import datetime

from django.db.models import Q, Sum
from django.utils import timezone
from django.views import generic

from apps.transaction.constants import TRANSACTION_FEED_PAGE_SIZE
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionFeedMixin(TransactionBaseContext):
    paginate_by = TRANSACTION_FEED_PAGE_SIZE

    def get_search_query(self) -> str:
        if not hasattr(self, "_search_query"):
            self._search_query = self.request.GET.get("q", "").strip()
        return self._search_query

    def get_base_queryset(self):
        return (
            ParentTransaction.objects.filter(room=self.request.room)
            .select_related("paid_by", "currency", "category")
            .prefetch_related("child_transactions")
            .annotate(total_child_value=Sum("child_transactions__value"))
            .order_by("-paid_at", "-id")
        )

    def filter_queryset(self, queryset):
        search_query = self.get_search_query()
        if search_query:
            queryset = queryset.filter(
                Q(description__icontains=search_query) | Q(paid_by__name__icontains=search_query)
            )
        return queryset

    def apply_cursor(self, queryset):
        cursor_paid_at = self.request.GET.get("cursor_paid_at")
        cursor_id = self.request.GET.get("cursor_id")
        if not cursor_paid_at or not cursor_id:
            return queryset

        try:
            cursor_dt = datetime.fromisoformat(cursor_paid_at)
        except ValueError:
            return queryset

        if timezone.is_naive(cursor_dt):
            cursor_dt = timezone.make_aware(cursor_dt, timezone.get_current_timezone())

        try:
            cursor_pk = int(cursor_id)
        except (TypeError, ValueError):
            return queryset

        return queryset.filter(Q(paid_at__lt=cursor_dt) | (Q(paid_at=cursor_dt) & Q(id__lt=cursor_pk)))

    def get_feed_batch(self, queryset=None):
        queryset = queryset or self.get_base_queryset()
        queryset = self.filter_queryset(queryset)
        queryset = self.apply_cursor(queryset)
        transactions = list(queryset[: self.paginate_by])
        next_cursor = None

        if len(transactions) == self.paginate_by:
            last_transaction = transactions[-1]
            next_cursor = {"id": last_transaction.id, "paid_at": last_transaction.paid_at}

        return transactions, next_cursor

    def build_feed_context(self, *, initial_render: bool, queryset=None):
        transactions, next_cursor = self.get_feed_batch(queryset=queryset)
        return {
            "parent_transactions": transactions,
            "transaction_next_cursor": next_cursor,
            "transaction_initial_render": initial_render,
            "transaction_search_query": self.get_search_query(),
        }


class TransactionListView(TransactionFeedMixin, generic.TemplateView):
    template_name = "transaction/list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_queryset = self.get_base_queryset()
        total_count = base_queryset.count()
        context["transactions_available"] = total_count > 0
        context["transactions_total_count"] = total_count
        context.update(self.build_feed_context(initial_render=True, queryset=base_queryset))
        return context


class TransactionFeedView(TransactionFeedMixin, generic.TemplateView):
    template_name = "transaction/partials/_transaction_batch.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.build_feed_context(initial_render=False))
        return context
