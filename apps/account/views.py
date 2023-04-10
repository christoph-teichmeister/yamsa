from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.account.models import User


class UserProfileView(generic.DetailView):
    template_name = "account/detail.html"
    context_object_name = "user"
    model = User


class AuthenticateGuestUserView(generic.View):
    http_method_names = [
        "post",
        "options",
    ]

    def post(self, request, *args, **kwargs):
        room_id = self.request.POST.get("room_id")

        redirect_response = HttpResponseRedirect(
            redirect_to=reverse(viewname="room-detail", args=room_id)
        )

        if request.user.is_authenticated:
            return redirect_response

        user_id = self.request.POST.get("user_id")
        guest_user = User.objects.get(id=user_id)
        login(request=request, user=guest_user)

        return redirect_response


class LogOutUserView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request, *args, **kwargs):
        logout(request=request)
        return HttpResponseRedirect(redirect_to=reverse(viewname="core-welcome"))
