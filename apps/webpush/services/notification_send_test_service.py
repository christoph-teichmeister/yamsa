import re

from apps.webpush.dataclasses import TestNotification

_notification_list = []


class NotificationSendTestService:
    _outbox: list[TestNotification] = []

    class _ExceptionMessages:
        FILTER_WITH_NOT_PARAMS = "NotificationSendTestService.filter called without parameters"

    def _load_notification_outbox(self):
        global _notification_list
        self._outbox = _notification_list

    def empty(self):
        global _notification_list
        _notification_list = []
        self._load_notification_outbox()

    def all(self):
        self._load_notification_outbox()
        return self._outbox

    def first(self):
        self._load_notification_outbox()
        return self._outbox[0]

    def filter(self, user=None, head=None, body=None, click_url=None):
        # Ensure that outbox is up-to-date
        self._load_notification_outbox()

        if not any([user, head, body, click_url]):
            raise ValueError(self._ExceptionMessages.FILTER_WITH_NOT_PARAMS)

        match_list = []
        for notification in self._outbox:
            # Check conditions
            match = True
            if user and user != notification.recipient:
                match = False
            if head and not re.search(head, str(notification.payload.head)):
                match = False
            if body and not re.search(body, str(notification.payload.body)):
                match = False
            if click_url and click_url not in notification.payload.click_url:
                match = False

            # Add email if all set conditions are valid
            if match:
                match_list.append(notification)

        return match_list
