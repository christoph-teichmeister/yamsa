from apps.room.views.mixins.dashboard_context import DashboardBaseContext


class DebtBaseContext(DashboardBaseContext):
    _active_tab = "debt"
