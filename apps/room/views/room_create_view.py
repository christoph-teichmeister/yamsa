from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.room.forms import RoomCreateForm
from apps.room.models import Room


class RoomCreateView(generic.CreateView):
    model = Room
    form_class = RoomCreateForm
    template_name = "room/create.html"

    def get_success_url(self):
        return reverse(
            viewname="room-detail", kwargs={"slug": self.object.slug}
        )

    def form_valid(self, form):
        created_room: Room = form.instance

        created_room.created_at = timezone.now()
        created_room.created_by = self.request.user

        ret = super().form_valid(form)

        created_room.users.add(self.request.user)

        return ret
