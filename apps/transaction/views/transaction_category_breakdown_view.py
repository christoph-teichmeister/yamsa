from collections import OrderedDict
from decimal import Decimal
from urllib.parse import urlencode

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.formats import number_format
from django.utils.translation import ngettext
from django.views import generic

from apps.transaction.constants import (
    CHART_SMALL_SLICE_BUCKET_COLOR,
    CHART_SMALL_SLICE_MINIMUM_BUCKET_SIZE,
    CHART_SMALL_SLICE_SHARE_THRESHOLD,
)
from apps.transaction.models import ParentTransaction
from apps.transaction.views.mixins.transaction_base_context import TransactionBaseContext


class TransactionCategoryBreakdownView(TransactionBaseContext, generic.TemplateView):
    template_name = "transaction/category_breakdown.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        breakdown_qs = (
            ParentTransaction.objects.filter(room=self.request.room)
            .values(
                "currency__id",
                "currency__code",
                "currency__name",
                "currency__sign",
                "category__slug",
                "category__name",
                "category__emoji",
                "category__color",
            )
            .annotate(
                total_amount=Coalesce(
                    Sum("child_transactions__value"),
                    Value(0),
                    output_field=DecimalField(),
                )
            )
            .filter(total_amount__gt=0)
        )

        breakdown_by_currency = OrderedDict()
        for entry in breakdown_qs:
            currency_id = entry["currency__id"]
            if currency_id not in breakdown_by_currency:
                breakdown_by_currency[currency_id] = {
                    "currency": {
                        "id": currency_id,
                        "code": entry["currency__code"],
                        "name": entry["currency__name"],
                        "sign": entry["currency__sign"],
                    },
                    "categories": [],
                }

            breakdown_by_currency[currency_id]["categories"].append(
                {
                    "slug": entry["category__slug"],
                    "name": entry["category__name"],
                    "emoji": entry["category__emoji"],
                    "color": entry["category__color"] or "#6c757d",
                    "total_amount": entry["total_amount"],
                }
            )

        formatted_breakdowns = []
        for group in breakdown_by_currency.values():
            sorted_categories = sorted(group["categories"], key=lambda item: item["total_amount"], reverse=True)
            currency_sign = group["currency"]["sign"] or ""
            currency_code = group["currency"]["code"] or ""
            chart_points = self._build_chart_points(sorted_categories, currency_sign)
            for category in sorted_categories:
                category["filter_url"] = self._build_filter_url(category["slug"], currency_code)

            currency_id = group["currency"]["id"]
            chart_suffix = f"{currency_code}-{currency_id}"

            formatted_breakdowns.append(
                {
                    "currency": group["currency"],
                    "categories": sorted_categories,
                    "chart_data": chart_points,
                    "chart_container_id": f"transaction-category-breakdown-chart-{chart_suffix}",
                    "chart_data_id": f"transaction-category-breakdown-data-{chart_suffix}",
                }
            )

        formatted_breakdowns.sort(key=lambda entry: entry["currency"]["code"] or "")

        context.update(
            {
                "category_breakdown_by_currency": formatted_breakdowns,
                "category_breakdown_period": "All recorded transactions",
            }
        )
        return context

    def _build_filter_url(self, category_slug: str, currency_code: str) -> str:
        list_url = reverse("transaction:list", kwargs={"room_slug": self.request.room.slug})
        return f"{list_url}?{urlencode({'category': category_slug, 'currency': currency_code})}"

    def _format_amount(self, amount: Decimal, currency_sign: str) -> str:
        return f"{number_format(amount, decimal_pos=2, use_l10n=True, force_grouping=True)}{currency_sign}"

    def _build_chart_points(self, sorted_categories: list[dict], currency_sign: str) -> list[dict]:
        """
        Build the donut slices, collapsing slivers too thin to tap into one bucket.

        The legend keeps every category, so nothing becomes unreachable — only the chart trades
        exact slices for hit targets.
        """
        total_amount = sum(category["total_amount"] for category in sorted_categories)
        small_categories = [
            category
            for category in sorted_categories
            if total_amount > 0 and category["total_amount"] / total_amount < CHART_SMALL_SLICE_SHARE_THRESHOLD
        ]

        # Bucketing a single sliver only relabels it, so it stays a slice of its own.
        if len(small_categories) < CHART_SMALL_SLICE_MINIMUM_BUCKET_SIZE:
            small_categories = []

        small_category_slugs = {category["slug"] for category in small_categories}
        chart_points = [
            {
                "slug": category["slug"],
                "label": f"{category['emoji']} {category['name']}",
                "value": float(category["total_amount"]),
                "color": category["color"],
                "amount_label": self._format_amount(category["total_amount"], currency_sign),
            }
            for category in sorted_categories
            if category["slug"] not in small_category_slugs
        ]

        if small_categories:
            bucket_amount = sum(category["total_amount"] for category in small_categories)
            chart_points.append(
                {
                    "slug": None,
                    "label": ngettext(
                        "%(count)s more category",
                        "%(count)s more categories",
                        len(small_categories),
                    )
                    % {"count": len(small_categories)},
                    "value": float(bucket_amount),
                    "color": CHART_SMALL_SLICE_BUCKET_COLOR,
                    "amount_label": self._format_amount(bucket_amount, currency_sign),
                }
            )

        return chart_points
