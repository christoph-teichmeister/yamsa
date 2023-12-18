from django.conf import settings
from django.http import JsonResponse
from django.views import generic


class ManifestView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request, *args, **kwargs):
        return JsonResponse(data=settings.MANIFEST)
