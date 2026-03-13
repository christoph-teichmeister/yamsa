from dataclasses import dataclass

from apps.account.models import User
from apps.webpush.dataclasses.notification import Notification


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
