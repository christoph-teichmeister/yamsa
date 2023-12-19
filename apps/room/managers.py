from django.db.models import Manager

from apps.room.querysets import RoomQuerySet


class RoomManager(Manager):
    def get_queryset(self) -> RoomQuerySet:
        return RoomQuerySet(self.model, using=self._db)

    def visible_for(self, user):
        return self.get_queryset().visible_for(user)
