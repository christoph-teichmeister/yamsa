from django.db.models import F
from django.views import generic

from apps.account.models import User


class UserListForRoomHTMXView(generic.ListView):
    model = User
    context_object_name = "user_qs_for_room"
    template_name = "account/_list_for_room.html"

    def get_queryset(self):
        return (
            self.model.objects.filter(rooms__slug=self.request.room.slug)
            .values("name", "id", "is_guest")
            .annotate(user_has_seen_this_room=F("userconnectiontoroom__user_has_seen_this_room"))
            .order_by("user_has_seen_this_room", "name")
        )
