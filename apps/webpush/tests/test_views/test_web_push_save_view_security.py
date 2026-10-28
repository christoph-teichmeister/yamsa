import http
import json

import pytest
from django.http import HttpResponse
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.webpush.models import WebpushInformation
from apps.webpush.tests.factories import WebpushInformationFactory


@pytest.mark.django_db
class TestWebPushSaveViewSecurity:
    ENDPOINT = "https://webpush.example/push"

    @pytest.fixture(autouse=True)
    def _setup(self, authenticated_client: Client, user: User) -> None:
        user.wants_to_receive_webpush_notifications = True
        user.save()
        self.client = authenticated_client
        self.url = reverse("webpush:save")
        self.user = user

    def _post(self, status_type: str = "subscribe", client: Client | None = None, **extra: object) -> HttpResponse:
        payload = {
            "subscription": {"endpoint": self.ENDPOINT, "keys": {"auth": "a", "p256dh": "p"}},
            "browser": "firefox",
            "user_agent": "ua",
            "status_type": status_type,
            **extra,
        }
        return (client or self.client).post(self.url, data=json.dumps(payload), content_type="application/json")

    def test_user_in_body_cannot_override_session_user(self) -> None:
        victim = UserFactory(wants_to_receive_webpush_notifications=True)

        response = self._post(user=victim.pk)

        assert response.status_code == http.HTTPStatus.CREATED
        assert not victim.webpush_infos.exists()
        assert self.user.webpush_infos.filter(endpoint=self.ENDPOINT).count() == 1

    def test_user_in_subscription_keys_cannot_override_session_user(self) -> None:
        victim = UserFactory(wants_to_receive_webpush_notifications=True)
        payload = {
            "subscription": {"endpoint": self.ENDPOINT, "keys": {"auth": "a", "p256dh": "p", "user": victim.pk}},
            "browser": "firefox",
            "status_type": "subscribe",
        }

        self.client.post(self.url, data=json.dumps(payload), content_type="application/json")

        assert not victim.webpush_infos.exists()

    def test_unsubscribe_cannot_delete_another_users_subscription(self) -> None:
        victim_info = WebpushInformationFactory(endpoint=self.ENDPOINT)

        self._post("unsubscribe", user=victim_info.user_id)

        assert WebpushInformation.objects.filter(pk=victim_info.pk).exists()

    def test_anonymous_request_is_rejected(self) -> None:
        response = self._post(client=Client())

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert not WebpushInformation.objects.exists()

    @pytest.mark.parametrize(
        "body", ["not json", "[]", "null", '{"subscription": []}', '{"subscription": {"keys": 1}}']
    )
    def test_malformed_body_returns_bad_request(self, body: str) -> None:
        response = self.client.post(self.url, data=body, content_type="application/json")

        assert response.status_code == http.HTTPStatus.BAD_REQUEST

    def test_resubscribe_with_rotated_keys_does_not_duplicate(self) -> None:
        WebpushInformationFactory(user=self.user, endpoint=self.ENDPOINT, auth="old", p256dh="old", user_agent="old")

        self._post()

        infos = self.user.webpush_infos.filter(endpoint=self.ENDPOINT)
        assert infos.count() == 1
        assert infos.get().auth == "a"

    def test_endpoint_moves_to_the_account_that_subscribes_last(self) -> None:
        WebpushInformationFactory(endpoint=self.ENDPOINT)

        self._post()

        owners = WebpushInformation.objects.filter(endpoint=self.ENDPOINT).values_list("user", flat=True)
        assert list(owners) == [self.user.pk]

    def test_unsubscribe_deletes_own_subscription_without_creating_one(self) -> None:
        WebpushInformationFactory(user=self.user, endpoint=self.ENDPOINT)

        response = self._post("unsubscribe")

        assert response.status_code == http.HTTPStatus.ACCEPTED
        assert not WebpushInformation.objects.exists()

    def test_unsubscribe_without_existing_subscription_creates_nothing(self) -> None:
        self._post("unsubscribe")

        assert not WebpushInformation.objects.exists()
