import json

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.webpush.models import WebpushInformation


@pytest.mark.django_db
class TestWebPushSaveViewCsrf:
    @pytest.fixture(autouse=True)
    def _setup(self, user: User) -> None:
        user.wants_to_receive_webpush_notifications = True
        user.save()
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(user)
        self.payload = json.dumps(
            {
                "subscription": {"endpoint": "https://webpush.example/push", "keys": {"auth": "a", "p256dh": "p"}},
                "browser": "firefox",
                "user_agent": "ua",
                "status_type": "subscribe",
            }
        )

    def _post(self, **headers: str) -> HttpResponse:
        return self.client.post(reverse("webpush:save"), data=self.payload, content_type="application/json", **headers)

    def test_post_without_csrf_token_is_rejected(self) -> None:
        assert self._post().status_code == 403
        assert not WebpushInformation.objects.exists()

    def test_post_with_csrf_header_stores_the_subscription(self) -> None:
        self.client.get(reverse("account:login"))
        token = self.client.cookies["csrftoken"].value

        assert self._post(HTTP_X_CSRFTOKEN=token).status_code == 201
        assert WebpushInformation.objects.count() == 1
