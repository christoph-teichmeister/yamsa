from apps.account.models import User
from apps.room.models import Room


class PersonCandidateService:
    """
    Supplies the people an importer can map a file column onto.

    Deliberately not SuggestedGuestService: that one skips guests and caps at eight entries,
    which would hide the most common duplicate ("this person is already a guest in another
    of my rooms") and make the import create a second account for them.
    """

    def __init__(self, user: User):
        self.user = user

    def get_candidates(self) -> list[User]:
        room_ids = Room.objects.filter(users=self.user).values_list("id", flat=True)
        return list(
            User.objects.filter(rooms__id__in=list(room_ids)).exclude(pk=self.user.pk).distinct().order_by("name", "id")
        )

    def match_by_name(self, name: str, candidates: list[User] | None = None) -> User | None:
        """Return the candidate whose name equals the column heading, ignoring case and padding."""
        needle = name.strip().casefold()
        if not needle:
            return None
        for candidate in candidates if candidates is not None else self.get_candidates():
            if candidate.name.strip().casefold() == needle:
                return candidate
        return None
