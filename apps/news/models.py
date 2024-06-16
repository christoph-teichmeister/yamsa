from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin
from apps.news.managers.feed_item import FeedItemManager


class FeedItem(FullCleanOnSaveMixin, CommonInfo):
    class ActionChoices(models.IntegerChoices):
        CREATED = 1, "Created"
        MODIFIED = 2, "Modified"
        DELETED = 3, "Deleted"
        ELSE = 99, "Else"

    action = models.SmallIntegerField(choices=ActionChoices, default=ActionChoices.ELSE)
    text = models.CharField(max_length=100)

    room = models.ForeignKey("room.Room", related_name="news", on_delete=models.DO_NOTHING)

    objects = FeedItemManager()

    class Meta:
        verbose_name = "FeedItem"
        verbose_name_plural = "FeedItems"
        ordering = ("-id",)

    def __str__(self):
        return self.text
