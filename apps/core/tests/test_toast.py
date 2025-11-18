import json

from django.http import HttpResponse
from django.template import Template
from django.template.response import TemplateResponse
from django.test import RequestFactory, SimpleTestCase

from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.core.toast import ToastQueue
from apps.core.toast_constants import SUCCESS_TOAST_CLASS


class ToastQueueTests(SimpleTestCase):
    def test_consume_clears_entries_and_preserves_order(self):
        queue = ToastQueue()
        queue.success("Built")
        queue.error("Oops")

        payload = queue.as_trigger_payload()
        queued_toasts = payload["triggerToast"]
        self.assertEqual(queued_toasts[0]["message"], "Built")
        self.assertEqual(queued_toasts[1]["message"], "Oops")
        self.assertFalse(queue.has_entries())

        consumed = queue.consume()
        self.assertEqual(consumed[0]["type"], SUCCESS_TOAST_CLASS)
        self.assertEqual(consumed[1]["message"], "Oops")
        self.assertFalse(queue.has_entries())


class ToastMiddlewareTests(SimpleTestCase):
    def setUp(self):
        self.request_factory = RequestFactory()

    def test_template_response_context_contains_queued_toasts(self):
        def get_response(request):
            request.toast_queue.success("Context toast")
            return TemplateResponse(request, Template("<div></div>"), {})

        middleware = ToastMiddleware(get_response)
        request = self.request_factory.get("/")
        response = middleware(request)

        self.assertIn("queued_toasts", response.context_data)
        queued_toasts = response.context_data["queued_toasts"]
        self.assertEqual(queued_toasts[0]["message"], "Context toast")

    def test_htmx_header_includes_toast_payload_and_merges_existing(self):
        def get_response(request):
            request.toast_queue.success("Header toast")
            response = HttpResponse()
            response["HX-Trigger"] = json.dumps({"existing": "value"})
            return response

        middleware = ToastMiddleware(get_response)
        request = self.request_factory.post("/", HTTP_HX_REQUEST="true")
        response = middleware(request)

        trigger_payload = json.loads(response["HX-Trigger"])
        self.assertEqual(trigger_payload["existing"], "value")
        toast_entries = trigger_payload["triggerToast"]
        self.assertEqual(toast_entries[0]["message"], "Header toast")

        after_settle_payload = json.loads(response["HX-Trigger-After-Settle"])
        self.assertEqual(after_settle_payload["triggerToast"][0]["message"], "Header toast")
