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

    users = models.ManyToManyField(
        "account.User", through="room.UserTransactionsForRoom"
    )

    class Meta:
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class UserTransactionsForRoom(models.Model):
    paid_by = models.ForeignKey("account.User", on_delete=models.CASCADE)

    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    transaction = models.ForeignKey(
        "transaction.Transaction", on_delete=models.CASCADE, related_name="belongs_to"
    )

    class Meta:
        verbose_name = "User Transaction for Room"
        verbose_name_plural = "Users Transactions for Rooms"

    def __str__(self):
        return f"{self.paid_by} pays {self.transaction} from {self.room}"
