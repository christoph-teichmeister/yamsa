from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.utils.translation import gettext_lazy as _

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class RoomNotClosedRequiredMixin(AccessMixin):
    """Block unsafe (mutating) requests against a closed room."""

    closed_room_message = _("This room is closed. No changes can be made.")

    def dispatch(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        room = getattr(request, "room", None)
        if request.method not in SAFE_METHODS and room is not None and room.is_closed:
            # Not handle_no_permission(): behind RoomMembershipRequiredMixin in the MRO that name
            # resolves to the membership 403, which carries no closed-room message.
            return HttpResponseForbidden(self.closed_room_message)
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self) -> HttpResponse:
        return HttpResponseForbidden(self.closed_room_message)
