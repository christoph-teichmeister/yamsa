from django.views import generic

from apps.room.models import Room
from apps.room.views.mixins.dashboard_base_context import DashboardBaseContext


class RoomDashboardView(DashboardBaseContext, generic.DetailView):
    template_name = "room/dashboard.html"
    slug_url_kwarg = "room_slug"
    model = Room

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)

        if not self.request.user.is_anonymous:
            connection = self.object.userconnectiontoroom_set.filter(
                user_id=self.request.user.id, user_has_seen_this_room=False
            ).first()
            if connection is not None:
                connection.user_has_seen_this_room = True
                connection.save()

        return response
