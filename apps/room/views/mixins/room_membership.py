from django.contrib.auth.mixins import AccessMixin
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden
from django.shortcuts import resolve_url


class RoomMembershipRequiredMixin(AccessMixin):
    """Prevent access to room resources for non-members."""

    def dispatch(self, request, *args, **kwargs):
        """Allow only authenticated users who have seen the room."""
        self.request = request
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()

        connection, _ = user.has_seen_room(request.room.id)
        if connection is None and not user.is_superuser:
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        """Signal a forbidden response when membership checks fail."""
        request = getattr(self, "request", None)
        if request and not request.user.is_authenticated:
            return redirect_to_login(
                request.get_full_path(),
                resolve_url(self.get_login_url()),
                self.get_redirect_field_name(),
            )

        return HttpResponseForbidden()
