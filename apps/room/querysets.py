from django.db import models
from django.db.models import BooleanField, Exists, ExpressionWrapper, F, Max, OuterRef
from django.db.models.functions import Coalesce, Substr, Upper


class RoomQuerySet(models.QuerySet):
    def visible_for(self, user):
        if user.is_anonymous:
            return self.none()

        if user.is_superuser:
            return self.all()

        return self.filter(users=user)

    def annotate_user_is_in_room_for_user_id(self, user_id: int):
        from apps.account.models import User

        return self.annotate(
            user_is_in_room=ExpressionWrapper(
                Exists(User.objects.filter(id=user_id, rooms=OuterRef("id"))),
                output_field=BooleanField(),
            ),
        )

    def annotate_last_transaction_lastmodified_at_date(self):
        return self.annotate(last_transaction_created_at_date=Max("parent_transactions__lastmodified_at"))

    def annotate_last_activity(self):
        """Annotate each room with when it was last used, from two angles.

        ``last_transaction_at`` is when the room's most recent transaction was paid, or NULL
        for a room that has none - it is what a room list may show, because a room without
        transactions has no last transaction to name.

        ``last_activity`` is the same value with the room's own lastmodified_at as a fallback,
        so every room can be ordered most-recently-used-first and a freshly created one starts
        at the top instead of at the bottom.

        Both read paid_at, never lastmodified_at: correcting the amount of a transaction from
        last year is bookkeeping, and must not present that room as the one in use right now.
        """
        return self.annotate(
            last_transaction_at=Max("parent_transactions__paid_at"),
            last_activity=Coalesce(
                Max("parent_transactions__paid_at"),
                F("lastmodified_at"),
            ),
        )

    def annotate_capitalised_initials(self):
        return self.annotate(capitalised_initials=Upper(Substr("name", 1, 2)))

    def filter_status_open(self):
        """Return only open rooms."""
        from apps.room.models import Room

        return self.filter(status=Room.StatusChoices.OPEN)

    def filter_status_closed(self):
        """Return only closed rooms."""
        from apps.room.models import Room

        return self.filter(status=Room.StatusChoices.CLOSED)

    def filter_without_members(self):
        """Return rooms that currently have no users at all."""
        return self.filter(users__isnull=True)
