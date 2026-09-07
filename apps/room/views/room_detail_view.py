from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.forms import RoomEditForm
from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext


class RoomDetailView(RoomBaseContext, generic.DetailView):
    # The room reads and edits in the same place, so this template carries both states.
    template_name = "room/detail.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room

    @context
    @cached_property
    def form(self):
        return RoomEditForm(instance=self.object)

    @context
    @cached_property
    def open_debt_count(self):
        return self.object.debts.filter(settled=False).count()
