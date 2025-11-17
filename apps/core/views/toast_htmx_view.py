from __future__ import annotations

import time

from django.views import generic
from django_context_decorator import context

from apps.core.toast_constants import TOAST_TYPE_CLASSES


class ToastHTMXView(generic.TemplateView):
    # TODO CT: This is not used anywhere?

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
        return TOAST_TYPE_CLASSES.get(toast_type, TOAST_TYPE_CLASSES["info"])
