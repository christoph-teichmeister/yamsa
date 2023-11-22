from django.db.models import F
from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.account.models import User
from apps.room.models import Room


class UserListForRoomHTMXView(generic.ListView):
    model = User
    context_object_name = "room_users"
    template_name = "account/_list_for_room.html"

    @context
    @cached_property
    def room(self):
        return Room.objects.get(slug=self.kwargs.get("room_slug"))

    def get_queryset(self):
        return (
            self.model.objects.filter(rooms__slug=self.kwargs.get("room_slug"))
            .values("name", "id", "is_guest")
            .annotate(user_has_seen_this_room=F("userconnectiontoroom__user_has_seen_this_room"))
            .order_by("user_has_seen_this_room", "name")
        )
