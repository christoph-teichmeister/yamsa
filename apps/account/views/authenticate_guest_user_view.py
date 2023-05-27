from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from apps.account.models import User
from apps.room.models import UserConnectionToRoom


class AuthenticateGuestUserView(generic.View):
    http_method_names = [
        "post",
        "options",
    ]

    def post(self, request, *args, **kwargs):
        room_slug = self.request.POST.get("room_slug")
        guest_user = None

        redirect_response = HttpResponseRedirect(
            redirect_to=reverse(viewname="room-detail", kwargs={"slug": room_slug})
        )

        if request.user.is_authenticated:
            connection = UserConnectionToRoom.objects.get(
                user=request.user, room__slug=room_slug
            )
            connection.user_has_seen_this_room = True
            connection.save()
        else:
            user_id = self.request.POST.get("user_id")
            guest_user = User.objects.get(id=user_id)
            login(request=request, user=guest_user)

        connection = UserConnectionToRoom.objects.get(
            user=guest_user or request.user, room__slug=room_slug
        )
        connection.user_has_seen_this_room = True
        connection.save()

        return redirect_response
