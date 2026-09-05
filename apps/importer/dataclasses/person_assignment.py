from dataclasses import dataclass


@dataclass(frozen=True)
class PersonAssignment:
    """How one person column of the file maps onto a yamsa user."""

    ME = "me"
    EXISTING = "existing"
    GUEST = "guest"

    column: str
    kind: str
    user_id: int | None = None
    guest_name: str = ""
