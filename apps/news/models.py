from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin


class News(FullCleanOnSaveMixin, CommonInfo):
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=10000)
    room = models.ForeignKey("room.Room", related_name="news", on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ("-id",)

    def __str__(self):
        return f"{self.title}: {self.message[:20]}..."
