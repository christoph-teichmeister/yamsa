from django.utils import timezone
from django.views import generic

from apps.account.forms import GuestCreateForm
from apps.account.models import User
from apps.core import htmx
from apps.room.models import Room, UserConnectionToRoom


class GuestCreateView(htmx.FormHtmxResponseMixin, generic.CreateView):
    model = User
    form_class = GuestCreateForm
    template_name = "account/partials/_guest_add_modal.html"

    hx_trigger = "loadPeopleList"
    toast_success_message = "Guest created successfully!"
    toast_error_message = "There was an error creating the guest"

    def form_valid(self, form):
        created_guest: User = form.instance

        created_guest.created_at = timezone.now()
        created_guest.created_by = self.request.user

        response = super().form_valid(form)

        room_slug = self.request.POST.get("room_slug")
        UserConnectionToRoom.objects.create(user=created_guest, room=Room.objects.get(slug=room_slug))

        return response
