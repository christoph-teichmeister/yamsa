from unittest import mock

from model_bakery import baker
from pywebpush import WebPushException

from apps.core.tests.setup import BaseTestSetUp
from apps.webpush.models import WebpushInformation
from apps.webpush.services.notification_send_service import NotificationSendService


class NotificationSendServiceTestCase(BaseTestSetUp):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.webpush_info = baker.make(WebpushInformation, user=cls.user)

    def setUp(self):
        super().setUp()
        self.service = NotificationSendService()

    def test_webpush_exception_is_swallowed(self):
        exception = WebPushException("boom", response=mock.Mock(status_code=500))

        with mock.patch(
            "apps.webpush.services.notification_send_service.webpush",
            side_effect=exception,
        ):
            responses = self.service.send_notification_to_user(self.user, payload="{}", ttl=60)

        self.assertEqual(responses, [])

    def test_unexpected_exception_is_swallowed(self):
        with mock.patch(
            "apps.webpush.services.notification_send_service.webpush",
            side_effect=RuntimeError("network down"),
        ):
            responses = self.service.send_notification_to_user(self.user, payload="{}", ttl=60)

        self.assertEqual(responses, [])
