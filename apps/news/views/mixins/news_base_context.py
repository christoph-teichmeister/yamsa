from apps.room.views.mixins.dashboard_context import DashboardBaseContext


class NewsBaseContext(DashboardBaseContext):
    _active_tab = "news"
