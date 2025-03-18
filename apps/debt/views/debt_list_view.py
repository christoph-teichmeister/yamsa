from django.views import generic
from django_context_decorator import context

from apps.debt.models import Debt
from apps.debt.views.mixins.debt_base_context import DebtBaseContext
from apps.transaction.models import ParentTransaction


class DebtListView(DebtBaseContext, generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/list.html"

    @context
    @property
    def has_transactions(self):
        return ParentTransaction.objects.filter(room_id=self.request.room.id).exists()

    def get_queryset(self):
        return self.model.objects.filter(room_id=self.request.room.id).order_by(
            "settled", "currency__sign", "debitor__name"
        )
