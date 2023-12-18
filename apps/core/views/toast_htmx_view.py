import time

from django.views import generic
from django_context_decorator import context


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

        toast_type_dict = {
            "info": "text-bg-primary bg-gradient",
            "success": "text-bg-success bg-gradient",
            "warning": "text-bg-warning bg-gradient",
            "error": "text-bg-danger bg-gradient",
        }
        return toast_type_dict.get(toast_type)
