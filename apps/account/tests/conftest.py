import pytest
from django.test import RequestFactory
from django.test.client import Client

from apps.account.models import User


@pytest.fixture
def form_request():
    return RequestFactory().get("/")


@pytest.fixture
def hx_client(client: Client):
    def _hx_client(user: User) -> Client:
        client.defaults["HTTP_HX_REQUEST"] = "true"
        client.force_login(user)
        return client

    return _hx_client
