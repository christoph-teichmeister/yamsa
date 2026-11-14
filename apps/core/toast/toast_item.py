from dataclasses import dataclass


@dataclass(slots=True)
class ToastItem:
    message: str
    toast_type: str
    # A toast with an action stays until `duration_ms` is up and offers a button that POSTs to
    # `action_url`; all three are empty for a plain toast, which uses the default timeout.
    action_label: str = ""
    action_url: str = ""
    duration_ms: int = 0

    def as_payload(self) -> dict[str, str | int]:
        payload: dict[str, str | int] = {"message": self.message, "type": self.toast_type}
        if self.action_url:
            payload.update(action_label=self.action_label, action_url=self.action_url, duration_ms=self.duration_ms)
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, str | int]) -> "ToastItem":
        return cls(
            message=str(payload["message"]),
            toast_type=str(payload["type"]),
            action_label=str(payload.get("action_label", "")),
            action_url=str(payload.get("action_url", "")),
            duration_ms=int(payload.get("duration_ms", 0)),
        )
