import pytest
from django.test import Client, override_settings
from django.urls import path

import apps.config.urls as root_urls


def _boom(request):
    raise Exception("forced")  # noqa: EM101


@pytest.fixture
def boom_url():
    url_pattern = path("__test_boom__/", _boom)
    root_urls.urlpatterns.append(url_pattern)
    yield "/__test_boom__/"
    root_urls.urlpatterns.remove(url_pattern)


@override_settings(DEBUG=False)
def test_server_error_view_renders_with_request_in_context(boom_url):
    """Regression test for #YAMSA-46/#YAMSA-44: Django's default handler500 renders 500.html
    without a request in context, and 500.html's base template needs `request`, so the crash
    handler itself was raising VariableDoesNotExist."""
    response = Client(raise_request_exception=False).get(boom_url)

    assert response.status_code == 500
    assert b"Something went wrong" in response.content


@override_settings(DEBUG=False)
def test_server_error_view_skips_full_page_render_for_htmx(boom_url):
    """An htmx request never swaps in a non-2xx response, so the full 500.html render (with all
    its context-processor dependencies) is unnecessary risk for no benefit — htmx's own
    `htmx:afterRequest` handler already shows an error toast and leaves the current page in place."""
    response = Client(raise_request_exception=False).get(boom_url, HTTP_HX_REQUEST="true")

    assert response.status_code == 500
    assert response.content == b""
