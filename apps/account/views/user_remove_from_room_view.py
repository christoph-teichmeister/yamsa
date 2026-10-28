from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.views import UserListForRoomView
from apps.core.event_loop.runner import handle_message
from apps.room.views.mixins import RoomNotClosedRequiredMixin


class UserRemoveFromRoomView(RoomNotClosedRequiredMixin, UserListForRoomView):
    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        room = request.room
        if not request.user.is_authenticated or not room.room_users.filter(pk=request.user.pk).exists():
            return HttpResponseForbidden()

        user_to_be_removed = get_object_or_404(room.room_users, pk=kwargs.get("pk"))

        if not user_to_be_removed.can_be_removed_from_room(room_id=room.id):
            request.toast_queue.error(
                f'"{user_to_be_removed.name}" can not be removed from this room, because they still '
                f"have either transactions or open debts."
            )
            return super().get(request, *args, **kwargs)

        handle_message(
            RemoveUserFromRoom(
                context_data={
                    "room": room,
                    "user_to_be_removed": user_to_be_removed,
                    "user_requesting_removal": request.user,
                }
            )
        )

        if user_to_be_removed.id == request.user.id:
            return HttpResponseRedirect(redirect_to=reverse(viewname="core:welcome"))

        return super().get(request, *args, **kwargs)
