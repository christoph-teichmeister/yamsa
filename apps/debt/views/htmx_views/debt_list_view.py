from django.views import generic

from apps.debt.models import Debt
from apps.room.views.mixins.room_specific_mixin import RoomSpecificMixin


class DebtListHTMXView(RoomSpecificMixin, generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/_list.html"

    def get_queryset(self):
        return self.model.objects.filter_for_room_id(room_id=self.request.room.id).order_by(
            "settled", "currency__sign", "debitor__username"
        )
