from apps.room.views.mixins.dashboard_context import DashboardBaseContext


class RoomBaseContext(DashboardBaseContext):
    _active_tab = "room"
