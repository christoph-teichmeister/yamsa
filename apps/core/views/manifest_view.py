from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import generic


class ManifestView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        return JsonResponse(data=settings.MANIFEST)
