"""Mixins related to room membership enforcement."""

from django.contrib.auth.mixins import AccessMixin
from django.http import HttpResponseForbidden


class RoomMembershipRequiredMixin(AccessMixin):
    """Prevent access to room resources for non-members."""

    def dispatch(self, request, *args, **kwargs):
        """Allow only authenticated users who have seen the room."""
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()

        connection, _ = user.has_seen_room(request.room.id)
        if connection is None and not user.is_superuser:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        """Signal a forbidden response when membership checks fail."""
        return HttpResponseForbidden()
