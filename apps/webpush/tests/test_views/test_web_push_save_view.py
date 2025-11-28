import http
import json
from unittest import mock

from django.test import RequestFactory
from django.urls import reverse

from apps.core.tests.setup import BaseTestSetUp
from apps.webpush.views import WebPushSaveView


class WebPushSaveViewTestCase(BaseTestSetUp):
    def setUp(self):
        super().setUp()
        self.url = reverse("webpush:save")
        self.factory = RequestFactory()
        self.client.force_login(self.user)

    def _build_payload(self, status_type: str) -> dict:
        return {
            "subscription": {
                "endpoint": "https://webpush.example/push",
                "keys": {"auth": "auth-string", "p256dh": "p256dh-string"},
            },
            "browser": "firefox",
            "user_agent": "yamsa-webpush-test",
            "status_type": status_type,
        }

    def _post(self, status_type: str):
        payload = self._build_payload(status_type)
        return self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_subscribe_status_returns_created(self):
        response = self._post("subscribe")

        self.assertEqual(response.status_code, http.HTTPStatus.CREATED)

    def test_unsubscribe_status_returns_accepted(self):
        response = self._post("unsubscribe")

        self.assertEqual(response.status_code, http.HTTPStatus.ACCEPTED)

    def test_form_valid_rejects_unknown_status_type(self):
        view = WebPushSaveView()
        request = self.factory.post(self.url)
        request.user = self.user
        view.request = request

        form = mock.Mock()
        form.cleaned_data = {"status_type": "unexpected"}
        form.save_or_delete = mock.Mock()

        response = view.form_valid(form)

        self.assertEqual(response.status_code, http.HTTPStatus.BAD_REQUEST)
        self.assertEqual(response.content, b"Unknown status_type")
        form.save_or_delete.assert_called_once()
