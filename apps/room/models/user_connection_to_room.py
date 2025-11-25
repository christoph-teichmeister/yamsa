from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.core.models.mixins.emit_model_created_event_on_save import EmitModelCreatedEventOnSaveMixin


class UserConnectionToRoom(EmitModelCreatedEventOnSaveMixin, FullCleanOnSaveMixin, CommonInfo):
    user = models.ForeignKey("account.User", on_delete=models.CASCADE)
    room = models.ForeignKey("room.Room", on_delete=models.CASCADE)
    user_has_seen_this_room = models.BooleanField(default=False)

    class Meta:
        verbose_name = _lazy("User-Connection to Room")
        verbose_name_plural = _lazy("User-Connections to Rooms")

    def __str__(self):
        return _("{user} belongs to {room}").format(user=self.user, room=self.room)

    @property
    def created_by_is_connection_user(self) -> bool:
        return self.created_by == self.user
