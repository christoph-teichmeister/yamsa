import json

import pytest
from django.http import HttpResponse

from apps.core.middleware.toast_middleware import ToastMiddleware
from apps.core.toast import ToastQueue
from apps.core.toast_constants import SUCCESS_TOAST_CLASS


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


@pytest.mark.urls("apps.core.tests.helpers.toast_urls")
def test_middleware_renders_toasts_into_a_full_page_load(db, client):
    response = client.get("/render/")

    assert response.content.decode() == "[Rendered toast]"


@pytest.mark.urls("apps.core.tests.helpers.toast_urls")
def test_middleware_leaves_htmx_toasts_to_the_headers(db, client):
    response = client.get("/render/", HTTP_HX_REQUEST="true")

    # The swapped-in page would show them a second time.
    assert response.content.decode() == ""
    assert json.loads(response["HX-Trigger"])["triggerToast"][0]["message"] == "Rendered toast"


def test_middleware_merges_toasts_into_htmx_headers(rf):
    def get_response(request) -> HttpResponse:
        request.toast_queue.success("Header toast")
        response = HttpResponse()
        response["HX-Trigger"] = json.dumps({"existing": "value"})
        return response

    middleware = ToastMiddleware(get_response)
    request = rf.post("/", HTTP_HX_REQUEST="true")
    response = middleware(request)

    trigger_payload = json.loads(response["HX-Trigger"])
    assert trigger_payload["existing"] == "value"
    toast_entries = trigger_payload["triggerToast"]
    assert toast_entries[0]["message"] == "Header toast"

    after_settle_payload = json.loads(response["HX-Trigger-After-Settle"])
    assert after_settle_payload["triggerToast"][0]["message"] == "Header toast"


@pytest.mark.urls("apps.core.tests.helpers.toast_urls")
def test_middleware_carries_toasts_across_a_redirect(db, client):
    redirect = client.post("/redirect/")

    assert redirect.status_code == 302
    assert "HX-Trigger" not in redirect
    assert client.get("/target/").content.decode() == "[Carried toast]"
    assert client.get("/target/").content.decode() == ""


@pytest.mark.urls("apps.core.tests.helpers.toast_urls")
def test_middleware_carries_toasts_across_a_redirect_htmx_follows(db, client):
    client.post("/redirect/", HTTP_HX_REQUEST="true")

    target = client.get("/target/", HTTP_HX_REQUEST="true")

    assert json.loads(target["HX-Trigger"])["triggerToast"][0]["message"] == "Carried toast"


@pytest.mark.urls("apps.core.tests.helpers.toast_urls")
def test_middleware_keeps_carried_toasts_away_from_prefetch_requests(db, client):
    client.post("/redirect/")

    assert client.get("/target/", HTTP_X_YAMSA_PREFETCH="1").content.decode() == ""
    assert client.get("/target/").content.decode() == "[Carried toast]"
