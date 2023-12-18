from http import HTTPStatus

from django.http import HttpResponse
from django.views import generic


class HealthcheckView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request, *args, **kwargs):
        return HttpResponse(status=HTTPStatus.OK)
