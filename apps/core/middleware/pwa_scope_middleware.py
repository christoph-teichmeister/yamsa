from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from apps.core.pwa_constants import SCOPE_HEADER_NAME
from apps.core.services.pwa_scope_service import resolve_scope


class PwaScopeHeaderMiddleware:
    """Tell the service worker which cache partition an HTML response may be stored in."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.get("Content-Type", "").startswith("text/html"):
            response[SCOPE_HEADER_NAME] = resolve_scope(getattr(request, "user", None))

        return response
