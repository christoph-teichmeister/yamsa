import json
from typing import Any

from django.http import HttpResponse

from apps.core.toast import ToastQueue


class ToastMiddleware:
    """Per-request toast queue that injects context data and HX headers."""

    HX_TRIGGER_HEADERS = ("HX-Trigger", "HX-Trigger-After-Settle")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.toast_queue = ToastQueue()
        response = self.get_response(request)
        queued_toasts = request.toast_queue.consume()
        if not queued_toasts:
            return response

        self._inject_context(response, queued_toasts)
        if self._is_htmx_request(request):
            self._attach_hx_triggers(response, queued_toasts)

        return response

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
