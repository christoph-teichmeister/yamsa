import http
import json

import pytest
from django.http import JsonResponse
from django.urls import reverse

from apps.account.tests.factories import UserPasskeyFactory

pytestmark = pytest.mark.django_db


class TestPasskeyRegBeginView:
    def test_get_requires_login(self, client):
        response = client.get(reverse("account:passkey-reg-begin"))

        assert response.status_code == http.HTTPStatus.FOUND
        assert "login" in response["Location"]

    def test_get_returns_400_when_passkey_already_exists(self, hx_client, user):
        UserPasskeyFactory(user=user)
        client = hx_client(user)
        response = client.get(reverse("account:passkey-reg-begin"))

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        data = json.loads(response.content)
        assert data["status"] == "ERR"

    def test_get_delegates_to_library_when_no_passkey(self, hx_client, user, monkeypatch):
        fake_state = {"challenge": "abc"}
        fake_options = {"publicKey": {"challenge": "abc"}}

        def fake_begin_registration(user, request):
            return fake_options, fake_state

        monkeypatch.setattr("passkeys.webauthn.begin_registration", fake_begin_registration)
        monkeypatch.setattr("passkeys.FIDO2.begin_registration", fake_begin_registration)

        client = hx_client(user)
        response = client.get(reverse("account:passkey-reg-begin"))

        assert response.status_code == http.HTTPStatus.OK
        assert isinstance(response, JsonResponse)
