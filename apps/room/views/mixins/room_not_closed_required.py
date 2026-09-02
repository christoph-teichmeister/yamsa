from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


class RoomNotClosedRequiredMixin(AccessMixin):
    """Block unsafe (mutating) requests against a closed room."""

    closed_room_message = "This room is closed. No changes can be made."

    def dispatch(self, request, *args, **kwargs):
        room = getattr(request, "room", None)
        if request.method not in SAFE_METHODS and room is not None and room.is_closed:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        return HttpResponseForbidden(self.closed_room_message)
