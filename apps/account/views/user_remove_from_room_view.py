import json

from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.models import User
from apps.account.views import UserListForRoomView
from apps.core.event_loop.runner import handle_message


class UserRemoveFromRoomView(UserListForRoomView):
    def post(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        user = User.objects.get(id=kwargs.get("pk"))

        if user.can_be_removed_from_room(room_id=self.request.room.id):
            handle_message(
                RemoveUserFromRoom(
                    context_data={
                        "room": self.request.room,
                        "user_to_be_removed": user,
                        "user_requesting_removal": self.request.user,
                    }
                )
            )
        else:
            response["HX-Trigger-After-Settle"] = json.dumps(
                {
                    "triggerToast": {
                        "message": f'"{user.name}" can not be removed from this room, because they still have either '
                        f"transactions or open debts.",
                        "type": "text-bg-danger bg-gradient",
                    }
                }
            )

        return response
