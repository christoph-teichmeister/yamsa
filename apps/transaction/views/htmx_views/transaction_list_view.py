from ambient_toolbox.view_layer import htmx_mixins
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.models import Room
from apps.transaction.models import ParentTransaction


class TransactionListHTMXView(generic.ListView):
    model = ParentTransaction
    context_object_name = "parent_transactions"
    template_name = "transaction/_list.html"

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
        return self.model.objects.filter(room=self._room)
