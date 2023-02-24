from ai_django_core.models import CommonInfo
from django.db import models


class Room(CommonInfo):
    class StatusChoices(models.IntegerChoices):
        OPEN = 1, "Open"
        CLOSED = 2, "Closed"

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    status = models.SmallIntegerField(
        choices=StatusChoices.choices, default=StatusChoices.OPEN
    )

    users = models.ManyToManyField("account.User", through="room.UserConnectionToRoom")

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class UserConnectionToRoom(models.Model):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "User-Connection to Room"
        verbose_name_plural = "User-Connections to Rooms"

    def __str__(self):
        return f"{self.user} belongs to {self.room}"
