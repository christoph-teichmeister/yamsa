import http

import pytest
from django.conf import LazySettings
from django.core.cache import cache
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.account.views.user_forgot_password_view import FORGOT_PASSWORD_IP_LIMIT

pytestmark = pytest.mark.django_db


class TestForgotPasswordIpLimit:
    @pytest.fixture(autouse=True)
    def _setup(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cache.clear()
        self.sent: list = []
        monkeypatch.setattr("apps.account.views.user_forgot_password_view.handle_message", self.sent.append)

    def _post(self, client: Client, email: str, **meta: str) -> HttpResponse:
        return client.post(reverse("account:forgot-password"), data={"email": email}, **meta)

    def _exhaust(self, client: Client, **meta: str) -> None:
        for i in range(FORGOT_PASSWORD_IP_LIMIT):
            self._post(client, f"nobody{i}@local.local", **meta)

    def test_limit_suppresses_mail_but_response_stays_identical(self, client: Client, user: User) -> None:
        unknown = self._post(client, "unknown@local.local", REMOTE_ADDR="10.0.0.1")
        self._exhaust(client, REMOTE_ADDR="10.0.0.1")

        limited_known = self._post(client, user.email, REMOTE_ADDR="10.0.0.1")
        limited_unknown = self._post(client, "unknown2@local.local", REMOTE_ADDR="10.0.0.1")

        assert not self.sent
        for response in (limited_known, limited_unknown):
            assert response.status_code == unknown.status_code == http.HTTPStatus.FOUND
            assert response["Location"] == unknown["Location"]

    def test_requests_below_the_limit_still_send(self, client: Client, user: User) -> None:
        self._post(client, user.email, REMOTE_ADDR="10.0.0.1")

        assert len(self.sent) == 1

    def test_counter_is_per_ip(self, client: Client, user: User) -> None:
        self._exhaust(client, REMOTE_ADDR="10.0.0.1")

        self._post(client, user.email, REMOTE_ADDR="10.0.0.2")

        assert len(self.sent) == 1

    def test_spoofed_forwarded_for_does_not_bypass_untrusted_header(self, client: Client, user: User) -> None:
        for i in range(FORGOT_PASSWORD_IP_LIMIT):
            self._post(client, f"nobody{i}@local.local", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR=f"6.6.6.{i}")

        self._post(client, user.email, REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="6.6.6.99")

        assert not self.sent

    def test_trusted_proxy_uses_address_the_proxy_appended(
        self, client: Client, user: User, settings: LazySettings
    ) -> None:
        settings.TRUSTED_PROXY_COUNT = 1
        # The client-supplied left entries vary; the entry our proxy appended is constant.
        for i in range(FORGOT_PASSWORD_IP_LIMIT):
            self._post(
                client, f"nobody{i}@local.local", REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR=f"6.6.6.{i}, 203.0.113.7"
            )

        self._post(client, user.email, REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="5.5.5.5, 203.0.113.7")
        assert not self.sent

        other_user = UserFactory()
        self._post(client, other_user.email, REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="5.5.5.5, 203.0.113.8")
        assert len(self.sent) == 1
