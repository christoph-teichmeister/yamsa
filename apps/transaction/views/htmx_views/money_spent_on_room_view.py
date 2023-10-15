from django.db.models import Sum
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.models import Room
from apps.transaction.models import ChildTransaction


class MoneySpentOnRoomView(generic.TemplateView):
    template_name = "transaction/partials/_money_spent_on_room.html"

    # Custom attributes
    _room = None

    def dispatch(self, request, *args, **kwargs):
        # Set room here, so that only one query is made and room is accessible throughout the other methods
        self._room = Room.objects.get(slug=self.kwargs.get("slug"))
        return super().dispatch(request, *args, **kwargs)

    def get_base_queryset(self):
        return ChildTransaction.objects.filter(parent_transaction__room=self._room)

    @context
    @cached_property
    def room(self):
        return self._room

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
