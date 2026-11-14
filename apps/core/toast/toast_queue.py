from apps.core.toast.toast_item import ToastItem
from apps.core.toast_constants import (
    ERROR_TOAST_CLASS,
    INFO_TOAST_CLASS,
    SUCCESS_TOAST_CLASS,
    WARNING_TOAST_CLASS,
)


class ToastQueue:
    """Simple queue that tracks toast messages and their CSS classes."""

    def __init__(self) -> None:
        self._items: list[ToastItem] = []

    def add(self, message: str, toast_type: str) -> None:
        """Add a custom toast entry regardless of the message type."""
        if not message:
            return
        self._items.append(ToastItem(message=message, toast_type=toast_type))

    def add_with_action(self, message: str, *, action_label: str, action_url: str, duration_ms: int) -> None:
        """Add a toast with one button that POSTs to `action_url`, e.g. an undo."""
        self._items.append(
            ToastItem(
                message=message,
                toast_type=SUCCESS_TOAST_CLASS,
                action_label=action_label,
                action_url=action_url,
                duration_ms=duration_ms,
            )
        )

    def add_payload(self, payload: dict[str, str | int]) -> None:
        """Re-queue a toast that `consume()` handed out, action included."""
        self._items.append(ToastItem.from_payload(payload))

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

    def consume(self) -> list[dict[str, str | int]]:
        """Return all queued toasts and clear the queue."""
        snapshot = self._snapshot()
        self._items.clear()
        return [item.as_payload() for item in snapshot]

    def as_trigger_payload(self) -> dict[str, list[dict[str, str | int]]]:
        """Return the trigger payload expected by HTMX headers."""
        return {"triggerToast": [item.as_payload() for item in self._snapshot()]}

    def has_entries(self) -> bool:
        return bool(self._items)
