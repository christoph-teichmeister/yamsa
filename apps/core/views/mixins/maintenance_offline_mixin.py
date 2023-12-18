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
    def called_by_get_user_offline_template_view(self):
        return isinstance(self, GetUserOfflineTemplateView)
