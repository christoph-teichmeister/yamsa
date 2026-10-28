from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse


class MaintenanceMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if settings.MAINTENANCE and request.path not in self._exempt_paths():
            return HttpResponseRedirect(redirect_to=reverse(viewname="core:maintenance"))

        return self.get_response(request)

    @staticmethod
    def _exempt_paths() -> set[str]:
        return {reverse("core:maintenance"), reverse("core:healthcheck")}
