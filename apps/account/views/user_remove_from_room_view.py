import json

from django.http import HttpResponseRedirect
from django.urls import reverse

from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.models import User
from apps.account.views import UserListForRoomView
from apps.core.event_loop.runner import handle_message
from apps.core.toast_constants import ERROR_TOAST_CLASS


class UserRemoveFromRoomView(UserListForRoomView):
    def post(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        user_to_be_removed = User.objects.get(id=kwargs.get("pk"))

        if user_to_be_removed.can_be_removed_from_room(room_id=self.request.room.id):
            handle_message(
                RemoveUserFromRoom(
                    context_data={
                        "room": self.request.room,
                        "user_to_be_removed": user_to_be_removed,
                        "user_requesting_removal": self.request.user,
                    }
                )
            )

            # If a user is removing themselves, redirect to room-list
            if user_to_be_removed.id == self.request.user.id:
                response = HttpResponseRedirect(redirect_to=reverse(viewname="core:welcome"))

        else:
            response["HX-Trigger-After-Settle"] = json.dumps(
                {
                    "triggerToast": {
                        "message": f'"{user_to_be_removed.name}" can not be removed from this room, because they still '
                        f"have either transactions or open debts.",
                        "type": ERROR_TOAST_CLASS,
                    }
                }
            )

        return response
