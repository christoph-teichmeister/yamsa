from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.account.forms import RegisterForm
from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.core.event_loop.runner import handle_message
from apps.room.constants import SHARED_ROOM_SLUG_SESSION_KEY
from apps.room.models import Room, UserConnectionToRoom


class RegisterUserView(generic.CreateView):
    template_name = "account/register.html"
    form_class = RegisterForm

    @context
    @property
    def email_from_invitation_email(self):
        return self.request.GET.get("with_email")

    @context
    @property
    def shared_room_slug(self) -> str | None:
        return self._room_slug_from_request() or self.request.session.get(SHARED_ROOM_SLUG_SESSION_KEY)

    def get_success_url(self):
        return reverse(viewname="core:welcome")

    def get_initial(self):
        return {
            **super().get_initial(),
            "id": self.request.GET.get("for_guest"),
            "email": self.request.GET.get("with_email"),
        }

    def form_valid(self, form):
        response = super().form_valid(form)

        # Immediately log the created user in
        self.request.user = self.object
        user = authenticate(request=self.request, email=self.object.email, password=self.object.password)
        login(request=self.request, user=user, backend="django.contrib.auth.backends.ModelBackend")

        self._join_shared_room_if_needed()

        # Send PostRegisterEmail
        handle_message(SendPostRegisterEmail(context_data={"user": self.request.user}))

        return response

    def _join_shared_room_if_needed(self) -> None:
        request_room_slug = self._room_slug_from_request()
        session_room_slug = self.request.session.pop(SHARED_ROOM_SLUG_SESSION_KEY, None)
        room_slug = request_room_slug or session_room_slug

        if not room_slug:
            return

        room = Room.objects.filter(slug=room_slug).first()
        if not room:
            return

        UserConnectionToRoom.objects.get_or_create(
            user=self.object,
            room=room,
            defaults={"user_has_seen_this_room": True},
        )

    def _room_slug_from_request(self) -> str | None:
        return self.request.POST.get("room_slug") or self.request.GET.get("room_slug")
