import re
from dataclasses import dataclass


@dataclass
class SuggestedGuest:
    user_id: int
    name: str
    email: str
    initials: str
    profile_picture_url: str | None
    is_friend: bool
    rooms_together: int

    @staticmethod
    def derive_initials(name: str) -> str:
        if not name:
            return ""

        parts = re.split(r"\s+", name.strip())
        initials = "".join(part[0] for part in parts if part)[:2]
        return initials.upper()

    @classmethod
    def from_user(cls, user, is_friend: bool, rooms_together: int) -> "SuggestedGuest":
        return cls(
            user_id=user.id,
            name=user.name,
            email=user.email,
            initials=cls.derive_initials(user.name),
            profile_picture_url=None if user.profile_picture._file is None else user.profile_picture_url,
            is_friend=is_friend,
            rooms_together=rooms_together,
        )
