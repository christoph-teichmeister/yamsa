from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden


class RoomMembershipRequiredMixin(AccessMixin):
    """Ensure the requesting user belongs to the room (or is a superuser)."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()

        connection, _ = user.has_seen_room(request.room.id)
        if connection is None and not user.is_superuser:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        return HttpResponseForbidden()
