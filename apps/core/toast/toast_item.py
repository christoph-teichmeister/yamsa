from dataclasses import dataclass


@dataclass(slots=True)
class ToastItem:
    message: str
    toast_type: str
