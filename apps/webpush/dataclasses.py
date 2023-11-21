from dataclasses import dataclass

import json
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ValidationError
from django.templatetags.static import static


@dataclass
class NotificationPayloadData:
    notification_click_url: str = ""
    action_click_urls: list[dict] = None

    def format_for_webpush(self):
        return {
            "notificationClickUrl": self.notification_click_url,
            "actionClickUrls": self.action_click_urls,
        }


@dataclass
class NotificationPayload:
    """Dataclass for the payload of a notification

    https://developer.mozilla.org/en-US/docs/Web/API/Notification
    https://web.dev/articles/push-notifications-display-a-notification
    """

    _default_icon_and_badge = settings.PROJECT_BASE_URL + staticfiles_storage.url("images/favicon.ico")

    head: str
    body: str
    data: NotificationPayloadData

    icon: str = _default_icon_and_badge
    badge: str = _default_icon_and_badge
    image: str = None

    actions: list[dict] = None
    vibrate: list[int] = None
    sound: str = None

    @property
    def _default_icon_and_badge(self):
        return settings.PROJECT_BASE_URL + static("images/favicon-32x32.png")

    def _validate_data_attr(self):
        for action_dict in self.actions:
            action_id = action_dict.get("action")
            if len(list(filter(lambda entry: entry.get("action") == action_id, self.data.action_click_urls))) == 0:
                raise ValidationError("Huen")

    def format_for_webpush(self):
        self._validate_data_attr()
        return json.dumps(
            {
                **self.__dict__,
                "data": self.data.format_for_webpush(),
            }
        )
