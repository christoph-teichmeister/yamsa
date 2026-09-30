from collections.abc import Callable

import pytest
from django.http import HttpRequest
from django.test import RequestFactory
from django.test.client import Client


@pytest.fixture
def form_request() -> HttpRequest:
    return RequestFactory().get("/")


@pytest.fixture
def hx_client(client) -> Callable:
    def _hx_client(user) -> Client:
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.force_login(user)
        return client

    return _hx_client
