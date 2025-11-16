from django.urls import reverse
from django.views import generic

from apps.account.views.mixins.account_base_context import AccountBaseContext
from apps.room.forms.user_connection_to_room_create_form import UserConnectionToRoomCreateForm
from apps.room.models import UserConnectionToRoom
from apps.room.services.suggested_guest_service import SuggestedGuestService


class UserConnectionToRoomCreateView(AccountBaseContext, generic.CreateView):
    model = UserConnectionToRoom
    form_class = UserConnectionToRoomCreateForm
    template_name = "room/userconnectiontoroom_create.html"

    def get_success_url(self):
        return reverse(viewname="account:list", kwargs={"room_slug": self.request.room.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["suggested_guests"] = SuggestedGuestService(user=self.request.user).get_suggested_guests()
        return context
