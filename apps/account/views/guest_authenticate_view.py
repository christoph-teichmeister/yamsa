from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views import generic

from apps.account.models import User
from apps.room.models import Room


class AuthenticateGuestUserView(generic.View):
    http_method_names = ["post", "options"]

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        try:
            room = get_object_or_404(Room, slug=request.POST.get("room_slug"))
        except ValidationError as error:
            # Room.slug is a UUID: a malformed value raises instead of simply matching nothing.
            raise Http404 from error

        if not request.user.is_authenticated:
            # Passwordless login: only guests of this very room may be picked, never a registered account.
            user_id = request.POST.get("user_id", "")
            guest_user = get_object_or_404(User, id=int(user_id) if user_id.isdigit() else 0, is_guest=True, rooms=room)
            login(request=request, user=guest_user, backend="django.contrib.auth.backends.ModelBackend")

        return HttpResponseRedirect(redirect_to=reverse(viewname="transaction:list", kwargs={"room_slug": room.slug}))
