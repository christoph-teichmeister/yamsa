from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import generic

from apps.core.event_loop.runner import handle_message
from apps.room.messages.commands.delete_room import DeleteRoom
from apps.room.views.mixins import RoomMembershipRequiredMixin


class RoomHardDeleteView(RoomMembershipRequiredMixin, generic.View):
    """Permanently delete a closed room and everything that exists only because of it.

    There is nothing to validate or persist, so this isn't a `ModelForm` and doesn't answer with
    the sheet the other room actions swap back in: once the room is gone there is nowhere left to
    render it into, so the response always leaves the room's URL space entirely. The caller must
    send the exact room name as `confirm_name` (case-sensitive, surrounding whitespace ignored).
    """

    open_room_message = _("Only a closed room can be deleted.")
    name_mismatch_message = _("The typed name does not match the room name.")

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        room = request.room

        if not room.can_be_deleted:
            return HttpResponseForbidden(self.open_room_message)

        # The dialog only disables its button; the server must not trust that.
        if request.POST.get("confirm_name", "").strip() != room.name.strip():
            return HttpResponseBadRequest(self.name_mismatch_message)

        handle_message(DeleteRoom(context_data={"room": room, "user_requesting_deletion": request.user}))

        return HttpResponseRedirect(reverse("core:welcome"))
