from __future__ import annotations

from django.views import generic
from django_context_decorator import context

from apps.core.toast_constants import TOAST_TYPE_CLASSES


class ToastHTMXView(generic.TemplateView):
    template_name = "shared_partials/toast.html"

    @context
    @property
    def queued_toasts(self) -> list[dict[str, str]]:
        toast_message = self.request.GET.get("toast_message")
        if not toast_message:
            return []

        toast_type = self.request.GET.get("toast_type", "info")
        toast_class = TOAST_TYPE_CLASSES.get(toast_type, TOAST_TYPE_CLASSES["info"])

        return [{"message": toast_message, "type": toast_class}]
