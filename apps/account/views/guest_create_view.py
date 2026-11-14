from django.db import transaction
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import generic

from apps.account.forms import GuestCreateForm
from apps.account.models import User
from apps.account.views.mixins.account_base_context import AccountBaseContext
from apps.room.models import UserConnectionToRoom
from apps.room.views.mixins import RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin


class GuestCreateView(RoomMembershipRequiredMixin, RoomNotClosedRequiredMixin, AccountBaseContext, generic.CreateView):
    model = User
    form_class = GuestCreateForm
    template_name = "account/create_guest.html"

    def form_valid(self, form: GuestCreateForm) -> HttpResponse:
        # A double submit would otherwise leave two identical guests in the room.
        if User.objects.filter(rooms=self.request.room, name__iexact=form.cleaned_data["name"]).exists():
            form.add_error("name", _("Someone with this name is already in this room"))
            return self.form_invalid(form)

        created_guest: User = form.instance

        created_guest.created_at = timezone.now()
        created_guest.created_by = self.request.user

        with transaction.atomic():
            response = super().form_valid(form)
            UserConnectionToRoom.objects.create(user=created_guest, room=self.request.room)

        return response

    def get_success_url(self) -> str:
        return reverse(viewname="account:list", kwargs={"room_slug": self.request.room.slug})
