import uuid

from django.contrib.auth import mixins
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views import generic

from apps.room.forms import RoomCreateForm
from apps.room.forms.user_connection_to_room_create_form import UserConnectionToRoomCreateForm
from apps.room.models import Room, UserConnectionToRoom
from apps.room.services.suggested_guest_service import SuggestedGuestService


class RoomCreateView(mixins.LoginRequiredMixin, generic.CreateView):
    model = Room
    form_class = RoomCreateForm
    template_name = "room/create.html"

    def get_success_url(self) -> str:
        return reverse(viewname="room:detail", kwargs={"room_slug": self.object.slug})

    def get_context_data(self, **kwargs: object) -> dict:
        context = super().get_context_data(**kwargs)
        context["suggested_guests"] = SuggestedGuestService(user=self.request.user).get_suggested_guests()
        context["creation_token"] = uuid.uuid4()
        context["dashboard_url"] = self._build_dashboard_url()
        return context

    def form_valid(self, form: RoomCreateForm) -> HttpResponse:
        token = self._creation_token()
        if token and (existing := Room.objects.filter(creation_token=token).first()):
            return self._redirect_to(existing)

        created_room: Room = form.instance

        created_room.created_at = timezone.now()
        created_room.created_by = self.request.user
        created_room.creation_token = token

        try:
            ret = super().form_valid(form)
        except (IntegrityError, ValidationError):
            # Lost the race against a concurrent POST of the same form (full_clean sees the committed
            # token as ValidationError, the unique index as IntegrityError): that request owns the room.
            existing = Room.objects.filter(creation_token=token).first()
            if token is None or existing is None:
                raise
            return self._redirect_to(existing)

        UserConnectionToRoom.objects.create(user=self.request.user, room=created_room)
        self._populate_suggested_guests(created_room)
        self.request.toast_queue.success(_("Room created."))

        return ret

    def _creation_token(self) -> uuid.UUID | None:
        try:
            return uuid.UUID(self.request.POST.get("creation_token", ""))
        except ValueError:
            return None

    def _redirect_to(self, room: Room) -> HttpResponse:
        return redirect("room:detail", room_slug=room.slug)

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
