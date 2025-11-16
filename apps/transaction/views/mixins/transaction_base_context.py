from apps.room.views.mixins.dashboard_context import DashboardBaseContext


class TransactionBaseContext(DashboardBaseContext):
    _active_tab = "transaction"
