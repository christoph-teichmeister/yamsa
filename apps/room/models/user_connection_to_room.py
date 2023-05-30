from django.db import models


class UserConnectionToRoom(models.Model):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    room = models.ForeignKey("room.Room", on_delete=models.CASCADE)
    user_has_seen_this_room = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User-Connection to Room"
        verbose_name_plural = "User-Connections to Rooms"

    def __str__(self):
        return f"{self.user} belongs to {self.room}"
