import http
import json
import re

import pytest
from django.db import connection
from django.urls import reverse
from playwright.sync_api import Page

from apps.account.models import User
from apps.account.tests.constants import DEFAULT_PASSWORD
from apps.account.tests.factories import UserFactory
from apps.webpush.models import WebpushInformation
from e2e.conftest import _login

ENDPOINT = "https://push.example/endpoint-1"


@pytest.mark.e2e
class TestWebpushSubscription:
    """The save endpoint as the browser's subscribe script calls it.

    Delivery itself needs a real push service and is not driven here; only what the endpoint stores is.
    """

    @staticmethod
    def _body(**extra: object) -> str:
        return json.dumps(
            {
                "subscription": {"endpoint": ENDPOINT, "keys": {"auth": "auth", "p256dh": "p256dh"}},
                "browser": "firefox",
                "user_agent": "e2e",
                "status_type": "subscribe",
                **extra,
            }
        )

    def _post(self, page: Page, base_url: str, body: str, with_csrf: bool = True) -> int:
        headers = {"Content-Type": "application/json"}
        if with_csrf:
            # The token the page's own subscribe script sends, as the template rendered it. Fetched
            # fresh because the DOM may come from the service worker cache, which holds an older token.
            # The HTML minifier may rewrite the quote style, so accept any.
            html = page.request.get(page.url).text()
            match = re.search(r"X-CSRFToken['\"]?:\s*[`'\"]([^`'\"]+)", html)
            assert match, "subscribe script renders no CSRF token"
            headers["X-CSRFToken"] = match.group(1)
        return page.request.post(f"{base_url}{reverse('webpush:save')}", data=body, headers=headers).status

    def test_an_anonymous_session_is_rejected_and_stores_nothing(self, page: Page, base_url: str) -> None:
        assert self._post(page, base_url, self._body(), with_csrf=False) == http.HTTPStatus.FORBIDDEN

        connection.close()
        assert not WebpushInformation.objects.exists()

    def test_a_signed_in_session_stores_the_subscription_for_itself_only(
        self, page: Page, base_url: str, profile_user: User
    ) -> None:
        profile_user.wants_to_receive_webpush_notifications = True
        profile_user.save()
        victim = UserFactory(wants_to_receive_webpush_notifications=True)
        _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

        status = self._post(page, base_url, self._body(user=victim.pk))

        assert status == http.HTTPStatus.CREATED
        connection.close()
        assert list(WebpushInformation.objects.values_list("user_id", flat=True)) == [profile_user.pk]

    def test_a_malformed_body_is_a_client_error(self, page: Page, base_url: str, profile_user: User) -> None:
        _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

        assert self._post(page, base_url, "not json") == http.HTTPStatus.BAD_REQUEST

    def test_a_signed_in_post_without_the_csrf_header_is_rejected(
        self, page: Page, base_url: str, profile_user: User
    ) -> None:
        profile_user.wants_to_receive_webpush_notifications = True
        profile_user.save()
        _login(page, base_url, profile_user.email, DEFAULT_PASSWORD)

        assert self._post(page, base_url, self._body(), with_csrf=False) == http.HTTPStatus.FORBIDDEN

        connection.close()
        assert not WebpushInformation.objects.exists()
