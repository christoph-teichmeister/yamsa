from django.contrib.auth import mixins
from django.db.models import OuterRef, ExpressionWrapper, Exists, BooleanField
from django.views import generic

from apps.account.models import User
from apps.room.models import Room


class RoomListView(mixins.LoginRequiredMixin, generic.ListView):
    model = Room
    context_object_name = "room_qs"
    template_name = "room/list.html"

    def get_queryset(self):
        return (
            self.model.objects.visible_for(user=self.request.user)
            .prefetch_related("users")
            .annotate(
                user_is_in_room=ExpressionWrapper(
                    Exists(User.objects.filter(id=self.request.user.id, rooms=OuterRef("id"))),
                    output_field=BooleanField(),
                ),
            )
            .order_by("-user_is_in_room", "status", "name")
            .values(
                "created_by__name",
                "description",
                "name",
                "slug",
                "status",
                "user_is_in_room",
            )
        )
