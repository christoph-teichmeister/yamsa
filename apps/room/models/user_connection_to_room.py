from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.core.models.mixins.emit_model_created_event_on_save import EmitModelCreatedEventOnSaveMixin


class UserConnectionToRoom(EmitModelCreatedEventOnSaveMixin, FullCleanOnSaveMixin, models.Model):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    room = models.ForeignKey("room.Room", on_delete=models.CASCADE)
    user_has_seen_this_room = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User-Connection to Room"
        verbose_name_plural = "User-Connections to Rooms"

    def __str__(self):
        return f"{self.user} belongs to {self.room}"
