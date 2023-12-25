from django.conf import settings
from django_context_decorator import context


class MaintenanceOrOfflineView:
    template_name = "core/_maintenance_or_offline.html"

    @context
    @property
    def is_in_maintenance(self):
        return settings.MAINTENANCE

    @context
    @property
    def called_by_offline_view(self):
        from apps.core.views import OfflineView

        return isinstance(self, OfflineView)
