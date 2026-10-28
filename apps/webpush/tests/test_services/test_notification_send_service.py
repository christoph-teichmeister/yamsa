from unittest import mock

import pytest
from pywebpush import WebPushException

from apps.account.models import User
from apps.webpush.services.notification_send_service import PUSH_TIMEOUT_SECONDS, NotificationSendService
from apps.webpush.services.notification_send_test_service import NotificationSendTestService
from apps.webpush.tests.factories import WebpushInformationFactory


@pytest.fixture
def notification_send_service(user: User) -> NotificationSendService:
    WebpushInformationFactory(user=user)
    return NotificationSendService()


@pytest.mark.django_db
class TestNotificationSendService:
    def test_webpush_exception_is_swallowed(
        self, notification_send_service: NotificationSendTestService, user: User
    ) -> None:
        exception = WebPushException("boom", response=mock.Mock(status_code=500))

        with mock.patch(
            "apps.webpush.services.notification_send_service.webpush",
            side_effect=exception,
        ):
            responses = notification_send_service.send_notification_to_user(user, payload="{}", ttl=60)

        assert responses == []

    def test_unexpected_exception_is_swallowed(
        self, notification_send_service: NotificationSendTestService, user: User
    ) -> None:
        with mock.patch(
            "apps.webpush.services.notification_send_service.webpush",
            side_effect=RuntimeError("network down"),
        ):
            responses = notification_send_service.send_notification_to_user(user, payload="{}", ttl=60)

        assert responses == []

    def test_push_call_has_a_timeout(self, notification_send_service: NotificationSendService, user: User) -> None:
        with mock.patch("apps.webpush.services.notification_send_service.webpush") as mocked_webpush:
            notification_send_service.send_notification_to_user(user, payload="{}", ttl=60)

        assert mocked_webpush.call_args.kwargs["timeout"] == PUSH_TIMEOUT_SECONDS

    def test_gone_subscription_is_deleted_and_not_reported_as_response(
        self, notification_send_service: NotificationSendService, user: User
    ) -> None:
        exception = WebPushException("gone", response=mock.Mock(status_code=410))

        with mock.patch("apps.webpush.services.notification_send_service.webpush", side_effect=exception):
            responses = notification_send_service.send_notification_to_user(user, payload="{}", ttl=60)

        assert responses == []
        assert not user.webpush_infos.exists()
