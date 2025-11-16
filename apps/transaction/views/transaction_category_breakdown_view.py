from collections import OrderedDict

from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce
from django.views import generic

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
            chart_points = [
                {
                    "slug": category["slug"],
                    "label": f"{category['emoji']} {category['name']}",
                    "value": float(category["total_amount"]),
                    "color": category["color"],
                }
                for category in sorted_categories
            ]

            currency_code = group["currency"]["code"] or ""
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
