from apps.room.views.mixins.dashboard_base_context import DashboardBaseContext


class TransactionBaseContext(DashboardBaseContext):
    _active_tab = "transaction"
