from unittest import mock

import pytest
from pywebpush import WebPushException

from apps.webpush.services.notification_send_service import NotificationSendService
from apps.webpush.tests.factories import WebpushInformationFactory


@pytest.fixture
def notification_send_service(user):
    WebpushInformationFactory(user=user)
    return NotificationSendService()


@pytest.mark.django_db
class TestNotificationSendService:
    def test_webpush_exception_is_swallowed(self, notification_send_service, user):
        exception = WebPushException("boom", response=mock.Mock(status_code=500))

        with mock.patch(
            "apps.webpush.services.notification_send_service.webpush",
            side_effect=exception,
        ):
            responses = notification_send_service.send_notification_to_user(user, payload="{}", ttl=60)

        assert responses == []

    def test_unexpected_exception_is_swallowed(self, notification_send_service, user):
        with mock.patch(
            "apps.webpush.services.notification_send_service.webpush",
            side_effect=RuntimeError("network down"),
        ):
            responses = notification_send_service.send_notification_to_user(user, payload="{}", ttl=60)

        assert responses == []
