from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic

from apps.account.models import User
from apps.room.models import Room


class AuthenticateGuestUserView(generic.View):
    """Two-step passwordless guest login: the picker POST shows a confirm page, only the confirm POST logs in."""

    http_method_names = ["post", "options"]
    confirm_template_name = "account/guest_login_confirm.html"

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
            # Logging in acts as that person, so a picker submit alone (possibly a misclick) must not do it.
            if request.POST.get("confirm") != "1":
                return render(request, self.confirm_template_name, {"room": room, "guest_user": guest_user})
            login(request=request, user=guest_user, backend="django.contrib.auth.backends.ModelBackend")

        return HttpResponseRedirect(redirect_to=reverse(viewname="transaction:list", kwargs={"room_slug": room.slug}))
