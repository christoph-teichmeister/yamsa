import pytest
from django.test import RequestFactory


@pytest.fixture
def form_request():
    return RequestFactory().get("/")


@pytest.fixture
def hx_client(client):
    def _hx_client(user):
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.force_login(user)
        return client

    return _hx_client
