from django.urls import reverse
from django.utils import timezone
from django.views import generic

from apps.account.forms import GuestCreateForm
from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext
from apps.room.models import Room, UserConnectionToRoom


class GuestCreateView(AccountBaseContext, generic.CreateView):
    model = User
    form_class = GuestCreateForm
    template_name = "account/create_guest.html"

    def form_valid(self, form):
        created_guest: User = form.instance

        created_guest.created_at = timezone.now()
        created_guest.created_by = self.request.user

        response = super().form_valid(form)

        room_slug = self.request.POST.get("room_slug")
        UserConnectionToRoom.objects.create(user=created_guest, room=Room.objects.get(slug=room_slug))

        return response

    def get_success_url(self):
        return reverse(viewname="account:list", kwargs={"room_slug": self.request.room.slug})
