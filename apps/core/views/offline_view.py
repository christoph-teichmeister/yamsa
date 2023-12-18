from django.views import generic

from apps.core.views import mixins


class OfflineView(mixins.MaintenanceOrOfflineView, generic.TemplateView):
    pass
