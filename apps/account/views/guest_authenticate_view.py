from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.account.models import User


class AuthenticateGuestUserView(generic.View):
    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        room_slug = self.request.POST.get("room_slug")

        redirect_response = HttpResponseRedirect(
            redirect_to=reverse(viewname="transaction:list", kwargs={"room_slug": room_slug})
        )

        if not request.user.is_authenticated:
            user_id = self.request.POST.get("user_id")
            guest_user = User.objects.get(id=user_id)
            login(request=request, user=guest_user, backend="django.contrib.auth.backends.ModelBackend")

        return redirect_response
