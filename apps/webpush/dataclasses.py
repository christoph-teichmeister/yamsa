import json
from dataclasses import dataclass

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static


@dataclass
class NotificationPayload:
    """Dataclass for the payload of a notification

    https://developer.mozilla.org/en-US/docs/Web/API/Notification
    https://web.dev/articles/push-notifications-display-a-notification
    """

    _default_icon_and_badge = settings.PROJECT_BASE_URL + staticfiles_storage.url("images/favicon.ico")

    head: str
    body: str

    click_url: str = ""

    icon: str = _default_icon_and_badge
    badge: str = _default_icon_and_badge
    image: str = None

    actions: list[dict] = None
    vibrate: list[int] = None
    sound: str = None

    @property
    def _default_icon_and_badge(self):
        return settings.PROJECT_BASE_URL + static("images/favicon-32x32.png")

    def _build_data(self) -> dict:
        action_click_urls = []

        for action in self.actions:
            action_click_urls.append({"action": action.get("action", ""), "url": action.pop("url", "")})

        return {"actionClickUrls": action_click_urls, "notificationClickUrl": self.click_url}

    def format_for_webpush(self):
        return json.dumps({**self.__dict__, "data": self._build_data()})
