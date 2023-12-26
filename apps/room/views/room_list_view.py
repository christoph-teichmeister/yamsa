from django.contrib.auth import mixins
from django.views import generic

from apps.room.models import Room


class RoomListView(mixins.LoginRequiredMixin, generic.ListView):
    model = Room
    context_object_name = "room_qs"
    template_name = "room/list.html"

    def get_queryset(self):
        return self.request.user.room_qs_for_list
