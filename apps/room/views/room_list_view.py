from django.views import generic

from apps.room.models import Room


class RoomListView(generic.ListView):
    model = Room
    context_object_name = "rooms"
    template_name = "room/list.html"

    def get_queryset(self):
        user = self.request.user

        if user.is_anonymous:
            return Room.objects.none()

        if user.is_superuser:
            return Room.objects.all()

        return Room.objects.filter(users=user)
