from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryAssignment:
    """How one source category maps onto a room category."""

    EXISTING = "existing"
    NEW = "new"

    label: str
    kind: str
    slug: str = ""
    name: str = ""
    emoji: str = ""
