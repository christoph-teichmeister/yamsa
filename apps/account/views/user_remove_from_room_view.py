import json

from apps.account.models import User
from apps.account.views import UserListForRoomView


class UserRemoveFromRoomView(UserListForRoomView):
    def post(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        user = User.objects.get(id=kwargs.get("pk"))

        if user.can_be_removed_from_room(room_id=self.request.room.id):
            # Convert to event loop
            self.rooms.remove(self.request.room)
        else:
            response["HX-Trigger-After-Settle"] = json.dumps(
                {
                    "triggerToast": {
                        "message": f'"{user.name}" can not be removed from this room, because they still have either '
                        f"transactions or open debts",
                        "type": "text-bg-danger bg-gradient",
                    }
                }
            )

        return response
