from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.account.forms import GuestCreateForm
from apps.account.models import User
from apps.room.models import Room, UserConnectionToRoom


class GuestCreateView(generic.CreateView):
    model = User
    form_class = GuestCreateForm
    template_name = "account/detail.html"

    def get_success_url(self):
        return reverse(viewname="room-detail", kwargs={"slug": self.request.POST.get("room_slug")})

    def form_valid(self, form):
        created_guest: User = form.instance

        created_guest.created_at = timezone.now()
        created_guest.created_by = self.request.user

        ret = super().form_valid(form)

        room_slug = self.request.POST.get("room_slug")
        UserConnectionToRoom.objects.create(user=created_guest, room=Room.objects.get(slug=room_slug))

        return ret
