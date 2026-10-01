from http import HTTPStatus

from django.http import HttpRequest, HttpResponse
from django.views import generic


class HealthcheckView(generic.View):
    http_method_names = ["get", "options"]

    def get(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        return HttpResponse(status=HTTPStatus.OK)
