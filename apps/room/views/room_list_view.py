from django.views import generic

from apps.room.models import Room


class RoomListView(generic.ListView):
    model = Room
    context_object_name = "room_qs"
    template_name = "room/list.html"

    def get_queryset(self):
        return (
            self.model.objects.visible_for(user=self.request.user)
            .order_by("status", "name")
            .values(
                "created_by",
                "description",
                "name",
                "slug",
                "status",
            )
        )
