import re

from apps.account.models import User
from apps.webpush.dataclasses import TestNotification

_notification_list = []


class NotificationSendTestService:
    _outbox: list[TestNotification] = []

    class _ExceptionMessages:
        FILTER_WITH_NOT_PARAMS = "NotificationSendTestService.filter called without parameters"

    def _load_notification_outbox(self) -> None:
        self._outbox = _notification_list

    def empty(self) -> None:
        _notification_list.clear()
        self._load_notification_outbox()

    def all(self) -> list[TestNotification]:
        self._load_notification_outbox()
        return self._outbox

    def first(self) -> TestNotification:
        self._load_notification_outbox()
        return self._outbox[0]

    def filter(
        self, user: User | None = None, head: str | None = None, body: str | None = None, click_url: str | None = None
    ) -> list[TestNotification]:
        # Ensure that outbox is up-to-date
        self._load_notification_outbox()

        if not any([user, head, body, click_url]):
            raise ValueError(self._ExceptionMessages.FILTER_WITH_NOT_PARAMS)

        return [
            notification
            for notification in self._outbox
            if (not user or user == notification.recipient)
            and (not head or re.search(head, str(notification.payload.head)))
            and (not body or re.search(body, str(notification.payload.body)))
            and (not click_url or click_url in notification.payload.click_url)
        ]
