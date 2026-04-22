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
        """Annotate each room with the timestamp of its most recent transaction,
        falling back to the room's own lastmodified_at so rooms without transactions
        still sort correctly (most-recently-active first)."""
        return self.annotate(
            last_activity=Coalesce(
                Max("parent_transactions__lastmodified_at"),
                F("lastmodified_at"),
            )
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
