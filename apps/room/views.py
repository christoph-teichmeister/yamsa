from django.views import generic

from apps.room.models import Room


class RoomListView(generic.ListView):
    template_name = "room/list.html"
    context_object_name = "rooms"
    model = Room

    def get_queryset(self):
        user = self.request.user

        if not user.is_anonymous:
            return Room.objects.filter(created_by=user)
        return Room.objects.all()


class RoomDetailView(generic.DetailView):
    template_name = "room/detail.html"
    context_object_name = "room"
    model = Room
