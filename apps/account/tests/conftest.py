import pytest
from django.test import RequestFactory
from django.test.client import Client


@pytest.fixture
def form_request():
    return RequestFactory().get("/")


@pytest.fixture
def hx_client(client):
    def _hx_client(user) -> Client:
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.force_login(user)
        return client

    return _hx_client
