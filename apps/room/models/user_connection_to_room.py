from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.core.models.mixins.emit_model_event_on_save import EmitModelEventOnSaveMixin


class UserConnectionToRoom(EmitModelEventOnSaveMixin, FullCleanOnSaveMixin, CommonInfo):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    room = models.ForeignKey("room.Room", on_delete=models.CASCADE)
    user_has_seen_this_room = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User-Connection to Room"
        verbose_name_plural = "User-Connections to Rooms"

    def __str__(self):
        return f"{self.user} belongs to {self.room}"

    @property
    def created_by_is_connection_user(self) -> bool:
        return self.created_by == self.user
