from apps.room.services.request_room_service import assign_room_to_request
from apps.room.views.room_dashboard_view import RoomDashboardView


class RoomShareView(RoomDashboardView):
    slug_field = "share_hash"
    slug_url_kwarg = "share_hash"

    def get_object(self, queryset=None):
        room = super().get_object(queryset)
        assign_room_to_request(self.request, room)
        return room
