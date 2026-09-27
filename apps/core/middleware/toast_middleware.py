import json
from typing import Any

from django.http import HttpResponse

from apps.core.pwa_constants import PREFETCH_HEADER_NAME
from apps.core.toast import ToastQueue


class ToastMiddleware:
    """Per-request toast queue that injects context data and HX headers."""

    HX_TRIGGER_HEADERS = ("HX-Trigger", "HX-Trigger-After-Settle")
    CARRIED_TOASTS_SESSION_KEY = "toast_middleware_carried_toasts"
    REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.toast_queue = ToastQueue()
        for toast in self._take_carried_toasts(request):
            request.toast_queue.add(toast["message"], toast["type"])

        response = self.get_response(request)
        queued_toasts = request.toast_queue.consume()
        if not queued_toasts:
            return response

        if response.status_code in self.REDIRECT_STATUS_CODES and hasattr(request, "session"):
            # A redirect renders nothing, and the browser (fetch included, so htmx too) follows it
            # without exposing its headers - the toasts are handed on to the request it leads to.
            request.session[self.CARRIED_TOASTS_SESSION_KEY] = queued_toasts
        elif self._is_htmx_request(request):
            self._attach_hx_triggers(response, queued_toasts)

        return response

    def process_template_response(self, request, response):
        # By the time __call__ gets the response back, the handler has rendered it, so the context
        # is only still open here. htmx requests are left to the headers: the toast script in a
        # swapped-in page runs again, and both would show every toast twice.
        if not self._is_htmx_request(request) and request.toast_queue.has_entries():
            self._inject_context(response, request.toast_queue.as_trigger_payload()["triggerToast"])
        return response

    def _take_carried_toasts(self, request) -> list[dict[str, str]]:
        # A background request that fills the offline cache would show them on a page nobody is
        # looking at.
        if request.headers.get(PREFETCH_HEADER_NAME):
            return []
        session = getattr(request, "session", None)
        # Checked before popping: pop() marks the session as modified, which would save it on
        # every request.
        if session is None or self.CARRIED_TOASTS_SESSION_KEY not in session:
            return []
        return session.pop(self.CARRIED_TOASTS_SESSION_KEY)

    def _inject_context(self, response: HttpResponse, queued_toasts: list[dict[str, str]]) -> None:
        context_data = getattr(response, "context_data", {}) or {}
        context = dict(context_data)
        queued = context.get("queued_toasts")
        if queued:
            queued.extend(queued_toasts)
        else:
            context["queued_toasts"] = list(queued_toasts)
        response.context_data = context

    def _is_htmx_request(self, request) -> bool:
        return bool(request.headers.get("HX-Request"))

    def _attach_hx_triggers(self, response: HttpResponse, queued_toasts: list[dict[str, str]]) -> None:
        for header in self.HX_TRIGGER_HEADERS:
            existing = self._parse_header(response.get(header))
            self._merge_trigger_payload(existing, queued_toasts)
            response[header] = json.dumps(existing)

    def _parse_header(self, header_value: Any) -> dict[str, Any]:
        if not header_value:
            return {}
        try:
            parsed = json.loads(header_value)
        except (TypeError, ValueError):
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _merge_trigger_payload(self, payload: dict[str, Any], queued_toasts: list[dict[str, str]]) -> None:
        existing = payload.get("triggerToast")
        if existing:
            if isinstance(existing, list):
                existing.extend(queued_toasts)
            else:
                payload["triggerToast"] = [existing, *queued_toasts]
        else:
            payload["triggerToast"] = list(queued_toasts)
