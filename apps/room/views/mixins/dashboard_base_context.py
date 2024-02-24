from functools import cached_property

from django_context_decorator import context

from apps.room.dataclasses import DashboardTab
from apps.room.services.dashboard_tab_service import DashboardTabService


class DashboardBaseContext:
    _active_tab: str = ""

    @context
    @cached_property
    def active_tab(self):
        return self.request.GET.get("active_tab", self._active_tab)

    @context
    @cached_property
    def dashboard_tabs(self) -> list[DashboardTab]:
        service = DashboardTabService(room=self.request.room)
        return service.get_tabs_as_list()
