from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse


class MaintenanceMiddleware:
    def __init__(self, get_response):
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request):
        if settings.MAINTENANCE and "maintenance" not in request.path:
            return HttpResponseRedirect(redirect_to=reverse(viewname="core:maintenance"))

        return self.get_response(request)
