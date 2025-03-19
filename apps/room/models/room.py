import uuid
from functools import cached_property

from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.room.managers import RoomManager


class Room(FullCleanOnSaveMixin, CommonInfo):
    class StatusChoices(models.IntegerChoices):
        OPEN = 1, "Open"
        CLOSED = 2, "Closed"

    slug = models.UUIDField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=50)
    status = models.SmallIntegerField(choices=StatusChoices.choices, default=StatusChoices.OPEN)

    preferred_currency = models.ForeignKey("currency.Currency", related_name="rooms", on_delete=models.DO_NOTHING)

    users = models.ManyToManyField(
        "account.User",
        through="room.UserConnectionToRoom",
        through_fields=(
            "room",
            "user",
        ),
    )

    objects = RoomManager()

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = uuid.uuid4()
        super().save(*args, **kwargs)

    @cached_property
    def room_users(self):
        from apps.account.models import User

        return User.objects.filter(room=self)

    @cached_property
    def has_guests(self):
        return self.room_users.filter(is_guest=True).exists()

    @cached_property
    def capitalised_initials(self):
        return self.name[:2].upper()

    @property
    def can_be_closed(self):
        return not self.debts.filter(settled=False).exists()
