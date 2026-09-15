from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.room.messages.commands.delete_room import DeleteRoom


class RoomHardDeleteView(generic.View):
    """Permanently delete a closed room and everything that exists only because of it.

    There is nothing to validate or persist, so this isn't a `ModelForm` and doesn't answer with
    the sheet the other room actions swap back in: once the room is gone there is nowhere left to
    render it into, so the response always leaves the room's URL space entirely.
    """

    open_room_message = _("Only a closed room can be deleted.")

    def post(self, request, *args, **kwargs):
        room = request.room

        if not room.can_be_deleted:
            return HttpResponseForbidden(self.open_room_message)

        handle_message(DeleteRoom(context_data={"room": room, "user_requesting_deletion": request.user}))

        return HttpResponseRedirect(reverse("core:welcome"))
