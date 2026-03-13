from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin


class RoomCategory(FullCleanOnSaveMixin, CommonInfo):
    room = models.ForeignKey("room.Room", related_name="room_categories", on_delete=models.CASCADE)
    category = models.ForeignKey("Category", related_name="room_category_map", on_delete=models.CASCADE)
    order_index = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("order_index", "id")
        constraints = [
            models.UniqueConstraint(fields=("room", "category"), name="unique_room_category"),
        ]

    def __str__(self) -> str:
        return f"{self.room} - {self.category}"
