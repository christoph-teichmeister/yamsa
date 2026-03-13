"""Helper classes for runner logging tests."""

import logging


class _CaptureHandler(logging.Handler):
    """Collect emitted log records for later inspection."""

    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
