import time

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views import generic
from django_context_decorator import context

from apps.news.models import News


class BaseView(generic.TemplateView):
    template_name = "core/base.html"

    def get(self, request, *args, **kwargs):
        return redirect(reverse(viewname="core-welcome"))


class WelcomePartialView(generic.TemplateView):
    template_name = "core/_welcome.html"

    def _get_news_base_qs(self):
        if self.request.user.is_authenticated:
            return News.objects.filter(
                room_id__in=self.request.user.room_set.values_list("id", flat=True)
            ).prefetch_related("comments")

        return News.objects.none()

    @context
    @property
    def news(self):
        return self._get_news_base_qs().exclude(highlighted=True)

    @context
    @property
    def highlighted_news(self):
        ret = self._get_news_base_qs().filter(highlighted=True).first()
        return ret


class MaintenanceOrOfflineView(generic.TemplateView):
    template_name = "core/_maintenance_or_offline.html"

    @context
    @property
    def is_in_maintenance(self):
        return settings.MAINTENANCE

    @context
    @property
    def called_by_get_user_offline_template_view(self):
        return isinstance(self, GetUserOfflineTemplateView)


class MaintenanceView(MaintenanceOrOfflineView):
    """Maintenance View is automatically injected as '' parent-url if settings.MAINTENANCE is true"""

    pass


class GetUserOfflineTemplateView(MaintenanceOrOfflineView):
    pass


class ManifestView(generic.View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(data=settings.MANIFEST)


class ServiceWorkerView(generic.TemplateView):
    template_name = "core/pwa/serviceworker.js"
    content_type = "application/x-javascript"


class ToastHTMXView(generic.TemplateView):
    template_name = "shared_partials/toast.html"

    @context
    @property
    def toast_id(self):
        return time.time()

    @context
    @property
    def toast_message(self):
        return self.request.GET.get("toast_message")

    @context
    @property
    def toast_type(self):
        # TODO CT: Extract these to some constant
        toast_type = self.request.GET.get("toast_type", "info")

        toast_type_dict = {
            "info": "text-bg-primary bg-gradient",
            "success": "text-bg-success bg-gradient",
            "warning": "text-bg-warning bg-gradient",
            "error": "text-bg-danger bg-gradient",
        }
        return toast_type_dict.get(toast_type)
