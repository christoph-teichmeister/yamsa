from django.db.models import F
from django.views import generic

from apps.account.models import User
from apps.room.views.mixins.room_specific_mixin import RoomSpecificMixin


class UserListForRoomHTMXView(RoomSpecificMixin, generic.ListView):
    model = User
    context_object_name = "room_users"
    template_name = "account/_list_for_room.html"

    def get_queryset(self):
        return (
            self.model.objects.filter(rooms__slug=self._room.slug)
            .values("name", "id", "is_guest")
            .annotate(user_has_seen_this_room=F("userconnectiontoroom__user_has_seen_this_room"))
            .order_by("user_has_seen_this_room", "name")
        )
