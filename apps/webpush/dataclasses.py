import json
from dataclasses import dataclass, field

from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.templatetags.static import static


@dataclass
class NotificationPayload:
    """Dataclass for the payload of a notification

    https://developer.mozilla.org/en-US/docs/Web/API/Notification
    https://web.dev/articles/push-notifications-display-a-notification

    Exemplary instantiation:

    NotificationPayload(
        head="Debug Notification",
        body="Click me, to go to the welcome page",
        actions=[
            {
                "action": "click-me-action",
                "type": "button",
                "title": "Go to user profile",
                "url": reverse(viewname="account-user-detail", kwargs={"pk": self.request.user.id}),
            },
        ],
        click_url=reverse(viewname="core-welcome"),
    )
    """

    head: str
    body: str

    click_url: str = ""

    icon: str = None
    badge: str = None
    image: str = None

    actions: list[dict] = field(default_factory=lambda: [])
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

    def _set_icon_and_badge_if_empty(self):
        default_icon_and_badge = settings.PROJECT_BASE_URL + staticfiles_storage.url("images/favicon.ico")

        if self.icon is None:
            self.icon = default_icon_and_badge

        if self.badge is None:
            self.badge = default_icon_and_badge

    def format_for_webpush(self):
        self._set_icon_and_badge_if_empty()
        return json.dumps({**self.__dict__, "data": self._build_data()})
