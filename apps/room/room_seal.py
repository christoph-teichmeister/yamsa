"""The room's signature seal - a shared-living object, not an initials avatar.

Every room gets a seal deterministically picked off its slug, so a room that has never had one
chosen still wears a stable mark wherever it is shown (the dashboard card, the room sheet's
header). A member can override that default with one of the same predefined icons, or with a
custom uploaded image - see Room.resolved_seal_icon/seal_image_url. See docs/ai/design.md's
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


def default_seal_icon(slug: UUID) -> str:
    return SEAL_ICONS[slug.int % len(SEAL_ICONS)]


def seal_tilt_deg(slug: UUID) -> int:
    return slug.int % 13 - 6
