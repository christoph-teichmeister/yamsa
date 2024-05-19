import json
from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static

from apps.account.models import User


@dataclass
class Notification:
    """Dataclass for a notification

    https://developer.mozilla.org/en-US/docs/Web/API/Notification
    https://web.dev/articles/push-notifications-display-a-notification

    Exemplary instantiation:
        notification = Notification(
            payload=Notification.Payload(
                head="Test Notification",
                body="Click me to open your profile page",
            ),
        )
    """

    @dataclass
    class Payload:
        """Dataclass for payload of a notification"""

        head: str
        body: str

        click_url: str = ""

        icon: str = None
        badge: str = None
        image: str = None

        actions: list[dict] = field(default_factory=list)
        vibrate: list[int] = None
        sound: str = None

        @property
        def _default_icon_and_badge(self):
            return settings.PROJECT_BASE_URL + static("images/32x32.webp")

        def _build_data(self) -> dict:
            action_click_urls = []

            for action in self.actions:
                action_click_urls.append({"action": action.get("action", ""), "url": action.pop("url", "")})

            return {"actionClickUrls": action_click_urls, "notificationClickUrl": self.click_url}

        def _set_icon_and_badge_if_empty(self):
            default_icon_and_badge = settings.PROJECT_BASE_URL + staticfiles_storage.url("images/favicon.ico")

            if self.icon is None:
                self.icon = default_icon_and_badge

            if self.badge is None:
                self.badge = default_icon_and_badge

        def format_for_webpush(self):
            self._set_icon_and_badge_if_empty()
            return json.dumps({**self.__dict__, "data": self._build_data()})

    payload: Payload
    ttl: int = 1000

    def send_to_user(self, user: User):
        # If the user does not want to receive webpush notifications, do not send them
        if not user.wants_to_receive_webpush_notifications:
            return

        from apps.webpush.services.notification_send_service import NotificationSendService

        service = NotificationSendService()
        service.send_notification_to_user(user, self.payload.format_for_webpush(), self.ttl)


@dataclass
class TestNotification(Notification):
    recipient = None

    def send_to_user(self, user: User):
        # If the user does not want to receive webpush notifications, do not send them
        if not user.wants_to_receive_webpush_notifications:
            return

        from apps.webpush.services.notification_send_test_service import _notification_list

        self.recipient = user
        _notification_list.append(self)
