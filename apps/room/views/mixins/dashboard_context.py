from functools import cached_property

from django_context_decorator import context

from apps.room.dataclasses import DashboardTab
from apps.room.services.dashboard_tab_service import DashboardTabService


class DashboardBaseContext:
    """Provide dashboard tabs, active tab tracking, and heartbeat-driven reminder checks."""

    _active_tab: str = "transaction"

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", self._active_tab)

    @context
    @cached_property
    def dashboard_tabs(self) -> list[DashboardTab]:
        service = DashboardTabService(room=self.request.room)
        return service.get_tabs_as_list()

    @context
    @cached_property
    def reminder_heartbeat(self):
        from apps.debt.services.payment_reminder_service import PaymentReminderService
        from apps.room.services.room_closure_reminder_service import RoomClosureReminderService

        PaymentReminderService().run_if_due()
        RoomClosureReminderService().run_if_due()
        return ""
