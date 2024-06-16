from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.news.managers.news import NewsManager


class News(FullCleanOnSaveMixin, CommonInfo):
    title = models.CharField(max_length=100)
    room = models.ForeignKey("room.Room", related_name="news", on_delete=models.DO_NOTHING)

    objects = NewsManager()

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ("-id",)

    def __str__(self):
        return self.title
