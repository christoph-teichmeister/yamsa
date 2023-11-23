from django.db.models import Sum
from django.views import generic
from django_context_decorator import context

from apps.room.views.mixins.room_specific_mixin import RoomSpecificMixin
from apps.transaction.models import ChildTransaction


class MoneySpentOnRoomView(RoomSpecificMixin, generic.TemplateView):
    template_name = "transaction/partials/_money_spent_on_room.html"

    def get_base_queryset(self):
        return ChildTransaction.objects.filter(parent_transaction__room=self._room)

    @context
    @property
    def money_spent_qs(self):
        return (
            self.get_base_queryset()
            .values("parent_transaction__paid_by__name", "parent_transaction__currency__sign")
            .annotate(total_spent=Sum("value"))
            .order_by("parent_transaction__paid_by__name")
        )

    @context
    @property
    def money_owed_qs(self):
        return (
            self.get_base_queryset()
            .values("paid_for__name", "parent_transaction__currency__sign")
            .annotate(total_owed=Sum("value"))
            .order_by("paid_for__name")
        )
