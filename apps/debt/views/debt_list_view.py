from django.views import generic

from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext


class DebtListView(DebtBaseContext, generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/list.html"

    def get_queryset(self):
        return self.model.objects.filter(room_id=self.request.room.id).order_by(
            "settled", "currency__sign", "debitor__username"
        )
