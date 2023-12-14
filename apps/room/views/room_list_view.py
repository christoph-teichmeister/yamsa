from django.views import generic

from apps.room.models import Room


class RoomListView(generic.ListView):
    model = Room
    context_object_name = "room_qs"
    template_name = "room/list.html"

    def get_queryset(self):
        # TODO CT: Move this to Queryset method
        user = self.request.user

        qs = Room.objects.filter(users=user)

        if user.is_anonymous:
            return Room.objects.none()

        if user.is_superuser:
            qs = Room.objects.all()

        return qs.order_by("status", "name")
