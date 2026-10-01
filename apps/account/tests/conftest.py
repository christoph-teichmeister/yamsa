from collections.abc import Callable

import pytest
from django.http import HttpRequest
from django.test import RequestFactory
from django.test.client import Client

from apps.account.models import User


@pytest.fixture
def form_request() -> HttpRequest:
    return RequestFactory().get("/")


@pytest.fixture
def hx_client(client: Client) -> Callable:
    def _hx_client(user: User) -> Client:
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.force_login(user)
        return client

    return _hx_client
