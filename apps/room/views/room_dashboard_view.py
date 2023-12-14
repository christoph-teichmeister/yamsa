from django.utils.functional import cached_property
from django.views import generic
from django_context_decorator import context

from apps.room.models import Room


class RoomDashboardView(generic.DetailView):
    template_name = "room/dashboard.html"
    slug_url_kwarg = "room_slug"
    model = Room

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", "transaction")

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
