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


@pytest.fixture
def superuser_htmx_client(superuser) -> Client:
    client = Client()
    client.defaults["HTTP_HX_REQUEST"] = "true"
    client.force_login(superuser)
    return client
