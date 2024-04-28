from django.urls import reverse
from django.views import generic

from apps.account.views.mixins.account_base_context import AccountBaseContext
from apps.room.forms.user_connection_to_room_create_form import UserConnectionToRoomCreateForm
from apps.room.models import UserConnectionToRoom


class UserConnectionToRoomCreateView(AccountBaseContext, generic.CreateView):
    model = UserConnectionToRoom
    form_class = UserConnectionToRoomCreateForm
    template_name = "room/userconnectiontoroom_create.html"

    def form_valid(self, form):
        response = super().form_valid(form)

        # UserConnectionToRoom.objects.create(user=created_guest, room=Room.objects.get(slug=room_slug))

        return response

    def get_success_url(self):
        return reverse(viewname="account:list", kwargs={"room_slug": self.request.room.slug})
