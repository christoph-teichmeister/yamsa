from dataclasses import dataclass

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage


@dataclass
class NotificationPayload:
    """Dataclass for the payload of a notification

    https://web.dev/articles/push-notifications-display-a-notification
    """

    _default_icon_and_badge = settings.PROJECT_BASE_URL + staticfiles_storage.url("images/favicon.ico")
    # _default_icon_and_badge = staticfiles_storage.url("images/favicon.ico")

    head: str
    body: str

    actions: list[dict]
    vibrate: list[int]
    sound: str

    icon: str = _default_icon_and_badge
    badge: str = _default_icon_and_badge
    image: str = ""
