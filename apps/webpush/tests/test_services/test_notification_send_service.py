from unittest import mock

import pytest
from model_bakery import baker
from pywebpush import WebPushException

from apps.webpush.models import WebpushInformation
from apps.webpush.services.notification_send_service import NotificationSendService


@pytest.fixture
def webpush_info(db, user):
    return baker.make(WebpushInformation, user=user)


@pytest.fixture
def notification_send_service(webpush_info):
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
