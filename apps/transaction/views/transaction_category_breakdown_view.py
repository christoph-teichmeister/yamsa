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
            ParentTransaction.objects.filter(
                room=self.request.room,
            )
            .values(
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
            .order_by("-total_amount")
        )

        breakdown = [
            {
                "slug": entry["category__slug"],
                "name": entry["category__name"],
                "emoji": entry["category__emoji"],
                "color": entry["category__color"] or "#6c757d",
                "total_amount": entry["total_amount"],
            }
            for entry in breakdown_qs
        ]

        chart_points = [
            {
                "slug": entry["slug"],
                "label": f"{entry['emoji']} {entry['name']}",
                "value": float(entry["total_amount"]),
                "color": entry["color"],
            }
            for entry in breakdown
        ]

        context.update(
            {
                "category_breakdown": breakdown,
                "category_breakdown_chart": chart_points,
                "category_breakdown_currency": self.request.room.preferred_currency.sign,
                "category_breakdown_period": "All recorded transactions",
            }
        )
        return context
