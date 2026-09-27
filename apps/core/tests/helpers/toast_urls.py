"""A URLconf that drives ToastMiddleware through Django's real handler, which renders a
TemplateResponse before the middleware's __call__ gets it back."""

from django.http import HttpResponseRedirect
from django.template import engines
from django.template.response import TemplateResponse
from django.urls import include, path

TOAST_TEMPLATE = engines["django"].from_string("{% for toast in queued_toasts %}[{{ toast.message }}]{% endfor %}")


def render_with_toast(request):
    request.toast_queue.success("Rendered toast")
    return TemplateResponse(request, TOAST_TEMPLATE, {})


def redirect_with_toast(request):
    request.toast_queue.success("Carried toast")
    return HttpResponseRedirect("/target/")


def target(request):
    return TemplateResponse(request, TOAST_TEMPLATE, {})


urlpatterns = [
    path("render/", render_with_toast),
    path("redirect/", redirect_with_toast),
    path("target/", target),
    # The rest of the stack reverses the app's own URL names.
    path("", include("apps.config.urls")),
]
