from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.debt.models import Debt
from apps.room.models import Room


class DebtListHTMXView(generic.ListView):
    model = Debt
    context_object_name = "debts"
    template_name = "debt/_list.html"

    # Custom attributes
    _room = None

    def dispatch(self, request, *args, **kwargs):
        # Set room here, so that only one query is made and room is accessible throughout the other methods
        self._room = Room.objects.get(slug=self.kwargs.get("room_slug"))
        return super().dispatch(request, *args, **kwargs)

    @context
    @cached_property
    def room(self):
        return self._room

    def get_queryset(self):
        return self.model.objects.filter_for_room_id(room_id=self._room.id).order_by(
            "settled", "currency__sign", "debitor__username"
        )
