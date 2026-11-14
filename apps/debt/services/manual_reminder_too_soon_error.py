from datetime import datetime


class ManualReminderTooSoonError(Exception):
    def __init__(self, next_available_at: datetime) -> None:
        super().__init__(next_available_at.isoformat())
        self.next_available_at = next_available_at
