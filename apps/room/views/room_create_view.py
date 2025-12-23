from django.contrib.auth import mixins
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.room.forms import RoomCreateForm
from apps.room.forms.user_connection_to_room_create_form import UserConnectionToRoomCreateForm
from apps.room.models import Room, UserConnectionToRoom
from apps.room.services.suggested_guest_service import SuggestedGuestService


class RoomCreateView(mixins.LoginRequiredMixin, generic.CreateView):
    model = Room
    form_class = RoomCreateForm
    template_name = "room/create.html"

    def get_success_url(self):
        return reverse(viewname="room:detail", kwargs={"room_slug": self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suggested_guests"] = SuggestedGuestService(user=self.request.user).get_suggested_guests()
        context["dashboard_url"] = self._build_dashboard_url()
        return context

    def form_valid(self, form):
        created_room: Room = form.instance

        created_room.created_at = timezone.now()
        created_room.created_by = self.request.user

        ret = super().form_valid(form)

        UserConnectionToRoom.objects.create(user=self.request.user, room=created_room)
        self._populate_suggested_guests(created_room)

        return ret

    def _populate_suggested_guests(self, created_room: Room) -> None:
        guest_emails = self.request.POST.getlist("suggested_guest_emails")
        if not guest_emails:
            return

        for email in guest_emails:
            data = {"email": email, "room_slug": created_room.slug}
            form = UserConnectionToRoomCreateForm(data=data)

            if form.is_valid():
                form.save()

    def _build_dashboard_url(self) -> str:
        base_url = reverse(viewname="core:welcome")
        query_string = self.request.GET.urlencode()
        if query_string:
            return f"{base_url}?{query_string}"
        return base_url
