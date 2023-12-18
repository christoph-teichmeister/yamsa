from apps.room.views.mixins.dashboard_base_context import DashboardBaseContext


class AccountBaseContext(DashboardBaseContext):
    _active_tab = "people"
