from django.views import generic
from django_context_decorator import context
from functools import cached_property

from apps.debt.models import Debt


class DebtListView(generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/list.html"

    def get_queryset(self):
        return self.model.objects.filter_for_room_id(room_id=self.request.room.id).order_by(
            "settled", "currency__sign", "debitor__username"
        )

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "debt")
