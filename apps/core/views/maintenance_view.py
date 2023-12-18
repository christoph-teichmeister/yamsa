from django.views import generic

from apps.core.views import mixins


class MaintenanceView(mixins.MaintenanceOrOfflineView, generic.TemplateView):
    """Maintenance View is automatically injected as '' parent-url if settings.MAINTENANCE is true"""

    pass
