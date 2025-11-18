from __future__ import annotations

from dataclasses import dataclass

from apps.core.toast_constants import (
    ERROR_TOAST_CLASS,
    INFO_TOAST_CLASS,
    SUCCESS_TOAST_CLASS,
    WARNING_TOAST_CLASS,
)


@dataclass(slots=True)
class ToastItem:
    message: str
    toast_type: str


class ToastQueue:
    """Simple queue that tracks toast messages and their CSS classes."""

    def __init__(self):
        self._items: list[ToastItem] = []

    def add(self, message: str, toast_type: str) -> None:
        """Add a custom toast entry regardless of the message type."""
        if not message:
            return
        self._items.append(ToastItem(message=message, toast_type=toast_type))

    def success(self, message: str) -> None:
        self.add(message, SUCCESS_TOAST_CLASS)

    def error(self, message: str) -> None:
        self.add(message, ERROR_TOAST_CLASS)

    def warning(self, message: str) -> None:
        self.add(message, WARNING_TOAST_CLASS)

    def info(self, message: str) -> None:
        self.add(message, INFO_TOAST_CLASS)

    def _snapshot(self) -> list[ToastItem]:
        return list(self._items)

    def consume(self) -> list[dict[str, str]]:
        """Return all queued toasts and clear the queue."""
        snapshot = self._snapshot()
        self._items.clear()
        return [{"message": item.message, "type": item.toast_type} for item in snapshot]

    def as_trigger_payload(self) -> dict[str, list[dict[str, str]]]:
        """Return the trigger payload expected by HTMX headers."""
        entries = self._snapshot()
        return {"triggerToast": [{"message": item.message, "type": item.toast_type} for item in entries]}

    def has_entries(self) -> bool:
        return bool(self._items)
