from __future__ import annotations

from django.views import generic
from django_context_decorator import context

from apps.core.toast_constants import TOAST_TYPE_CLASSES


class ToastHTMXView(generic.TemplateView):
    """
    HTMX-friendly fragment that renders the shared toast partial with payload data.

    The view simply forwards the GET parameters `toast_message` and `toast_type` into the
    shared `queued_toasts` context so the `shared_partials/toast.html` script can show the
    notification. Reusing this endpoint avoids having to duplicate the toast map or
    template across every action that wants to trigger a toast.

    Usage:
        1. Send an HTMX or fetch GET to `/core/toast/?toast_message=…&toast_type=…`.
        2. The response includes the toast markup plus `queued_toasts` JSON.
        3. The base template already listens for that payload and will display the toast.
        4. `toast_type` values come from `TOAST_TYPE_CLASSES` (`info`, `success`, `warning`, `error`).

    """

    # How to use:
    #   - URL helper: reverse("core:toast")
    #   - HTMX example: hx-get="{% url 'core:toast' %}?toast_message=Saved&toast_type=success"

    template_name = "shared_partials/toast.html"

    @context
    @property
    def queued_toasts(self) -> list[dict[str, str]]:
        """
        Convert the query parameters into a toast payload that matches the shared style map.
        """
        toast_message = self.request.GET.get("toast_message")
        if not toast_message:
            return []

        toast_type = self.request.GET.get("toast_type", "info")
        # fall back to the info class when the caller passes an unknown toast type key
        toast_class = TOAST_TYPE_CLASSES.get(toast_type, TOAST_TYPE_CLASSES["info"])

        return [{"message": toast_message, "type": toast_class}]
