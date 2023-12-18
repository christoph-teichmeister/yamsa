from django.db.models import F
from django.views import generic

from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext


class UserListForRoomView(AccountBaseContext, generic.ListView):
    model = User
    context_object_name = "user_qs_for_room"
    template_name = "account/list.html"

    def get_queryset(self):
        return (
            self.model.objects.filter(rooms__slug=self.request.room.slug)
            .values("name", "id", "is_guest")
            .annotate(user_has_seen_this_room=F("userconnectiontoroom__user_has_seen_this_room"))
            .order_by("user_has_seen_this_room", "name")
        )
