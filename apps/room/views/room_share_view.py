from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse

from apps.room.constants import SHARED_ROOM_SLUG_SESSION_KEY
from apps.room.services.request_room_service import assign_room_to_request
from apps.room.views.room_dashboard_view import RoomDashboardView


class RoomShareView(RoomDashboardView):
    slug_field = "share_hash"
    slug_url_kwarg = "share_hash"

    def get_object(self, queryset=None):
        room = super().get_object(queryset)
        assign_room_to_request(self.request, room)
        self.request.session[SHARED_ROOM_SLUG_SESSION_KEY] = str(room.slug)
        return room

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        room = self.get_object()

        if request.user.is_authenticated:
            connection, _ = request.user.has_seen_room(room.id)
            if connection is not None:
                return HttpResponseRedirect(redirect_to=reverse("transaction:list", kwargs={"room_slug": room.slug}))

        self.object = room
        context = self.get_context_data(object=room)
        return self.render_to_response(context)
