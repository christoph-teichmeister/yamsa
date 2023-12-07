import uuid

from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin


class Room(FullCleanOnSaveMixin, CommonInfo):
    class StatusChoices(models.IntegerChoices):
        OPEN = 1, "Open"
        CLOSED = 2, "Closed"

    slug = models.UUIDField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    status = models.SmallIntegerField(choices=StatusChoices.choices, default=StatusChoices.OPEN)

    preferred_currency = models.ForeignKey("currency.Currency", related_name="rooms", on_delete=models.DO_NOTHING)

    users = models.ManyToManyField("account.User", through="room.UserConnectionToRoom")

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = uuid.uuid4()
        super().save(*args, **kwargs)

    @property
    def can_be_closed(self):
        # TODO CT: Do this
        return False
