_notification_list = []


class NotificationSendTestService:
    _outbox = []

    class _ExceptionMessages:
        FILTER_WITH_NOT_PARAMS = "NotificationSendTestService.filter called without parameters"

    def _load_notification_outbox(self):
        self._outbox = _notification_list

    def all(self):
        self._load_notification_outbox()
        return self._outbox

    def filter(self, user=None, head=None, body=None, click_url=None, actions=None):
        # Ensure that outbox is up-to-date
        self._load_notification_outbox()

        if not any([user, head, body, click_url, actions]):
            raise ValueError(self._ExceptionMessages.FILTER_WITH_NOT_PARAMS)

        match_list = []
        for notification in self._outbox:
            # Check conditions
            match = True
            if user and user not in notification.to:
                match = False
            # if cc and cc not in email.cc:
            #     match = False
            # if bcc and bcc not in email.bcc:
            #     match = False
            # if subject and not re.search(subject, str(email.subject)):
            #     match = False

            # Add email if all set conditions are valid
            if match:
                match_list.append(notification)

        return match_list
