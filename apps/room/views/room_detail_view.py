from django.views import generic

from apps.room.models import Room
from apps.room.views.mixins.room_base_context import RoomBaseContext


class RoomDetailView(RoomBaseContext, generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    slug_url_kwarg = "room_slug"
    model = Room
