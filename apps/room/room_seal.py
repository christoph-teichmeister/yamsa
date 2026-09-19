"""The room's signature seal - a shared-living object, not an initials avatar.

Picked deterministically off the room's slug, so the same room always wears the same mark
wherever it is shown (the dashboard card, the room sheet's header). See docs/ai/design.md's
component patterns for the stamp itself.
"""

from uuid import UUID

SEAL_ICONS = (
    "key",
    "cup-hot",
    "lamp",
    "door-open",
    "leaf",
    "house-heart",
    "piggy-bank",
    "palette2",
)


def seal_icon(slug: UUID) -> str:
    return SEAL_ICONS[slug.int % len(SEAL_ICONS)]


def seal_tilt_deg(slug: UUID) -> int:
    return slug.int % 13 - 6
