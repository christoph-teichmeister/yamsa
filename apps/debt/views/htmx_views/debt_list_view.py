from django.views import generic
from django_context_decorator import context

from apps.debt.models import Debt


class DebtListHTMXView(generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/_list.html"

    def get_queryset(self):
        return self.model.objects.filter_for_room_id(room_id=self.request.room.id).order_by(
            "settled", "currency__sign", "debitor__username"
        )

    @context
    @property
    def room(self):
        # TODO CT: Fix room_url templatetag
        return self.request.room
