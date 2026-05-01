import http
import json

import pytest
from django.urls import reverse

from apps.account.constants import SESSION_TTL_SESSION_KEY

pytestmark = pytest.mark.django_db


class TestPasskeyLoginView:
    def test_post_with_valid_passkey_returns_ok_and_redirect(self, client, user, monkeypatch):
        monkeypatch.setattr("apps.account.backends.auth_complete", lambda request: user)

        session = client.session
        session["fido2_state"] = {"challenge": "fake"}
        session.save()

        response = client.post(
            reverse("account:passkey-auth-complete"),
            data={"passkeys": json.dumps({"id": "cred-id", "type": "public-key"})},
        )

        assert response.status_code == http.HTTPStatus.OK
        data = json.loads(response.content)
        assert data["status"] == "OK"
        assert "redirect" in data

    def test_post_with_invalid_passkey_returns_401(self, client, monkeypatch):
        monkeypatch.setattr("apps.account.backends.auth_complete", lambda request: None)

        session = client.session
        session["fido2_state"] = {"challenge": "fake"}
        session.save()

        response = client.post(
            reverse("account:passkey-auth-complete"),
            data={"passkeys": json.dumps({"id": "bad-cred", "type": "public-key"})},
        )

        assert response.status_code == http.HTTPStatus.UNAUTHORIZED
        data = json.loads(response.content)
        assert data["status"] == "ERR"

    def test_post_sets_session_ttl_on_success(self, client, user, monkeypatch):
        from django.conf import settings

        monkeypatch.setattr("apps.account.backends.auth_complete", lambda request: user)

        session = client.session
        session["fido2_state"] = {"challenge": "fake"}
        session.save()

        client.post(
            reverse("account:passkey-auth-complete"),
            data={"passkeys": json.dumps({"id": "cred-id", "type": "public-key"})},
        )

        assert client.session[SESSION_TTL_SESSION_KEY] == settings.SESSION_COOKIE_AGE
