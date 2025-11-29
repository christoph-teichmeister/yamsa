import json

import pytest
from django.http import HttpResponse
from django.template import Template
from django.template.response import TemplateResponse
from django.test import RequestFactory

from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.core.toast import ToastQueue
from apps.core.toast_constants import SUCCESS_TOAST_CLASS


@pytest.fixture
def request_factory():
    return RequestFactory()


def test_toast_queue_consumption_order_and_clears_entries():
    queue = ToastQueue()
    queue.success("Built")
    queue.error("Oops")

    payload = queue.as_trigger_payload()
    queued_toasts = payload["triggerToast"]
    assert queued_toasts[0]["message"] == "Built"
    assert queued_toasts[1]["message"] == "Oops"
    assert queue.has_entries()

    consumed = queue.consume()
    assert consumed[0]["type"] == SUCCESS_TOAST_CLASS
    assert consumed[1]["message"] == "Oops"
    assert not queue.has_entries()


def test_middleware_injects_toasts_into_template_context(request_factory):
    def get_response(request):
        request.toast_queue.success("Context toast")
        return TemplateResponse(request, Template("<div></div>"), {})

    middleware = ToastMiddleware(get_response)
    request = request_factory.get("/")
    response = middleware(request)

    assert "queued_toasts" in response.context_data
    queued_toasts = response.context_data["queued_toasts"]
    assert queued_toasts[0]["message"] == "Context toast"


def test_middleware_merges_toasts_into_htmx_headers(request_factory):
    def get_response(request):
        request.toast_queue.success("Header toast")
        response = HttpResponse()
        response["HX-Trigger"] = json.dumps({"existing": "value"})
        return response

    middleware = ToastMiddleware(get_response)
    request = request_factory.post("/", HTTP_HX_REQUEST="true")
    response = middleware(request)

    trigger_payload = json.loads(response["HX-Trigger"])
    assert trigger_payload["existing"] == "value"
    toast_entries = trigger_payload["triggerToast"]
    assert toast_entries[0]["message"] == "Header toast"

    after_settle_payload = json.loads(response["HX-Trigger-After-Settle"])
    assert after_settle_payload["triggerToast"][0]["message"] == "Header toast"
