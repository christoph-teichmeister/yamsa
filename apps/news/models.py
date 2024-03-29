from ambient_toolbox.models import CommonInfo
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin


class News(FullCleanOnSaveMixin, CommonInfo):
    highlighted = models.BooleanField(default=False)
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=10000)
    room = models.ForeignKey("room.Room", related_name="news", on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = (
            "highlighted",
            "-id",
        )

    def __str__(self):
        return f"{self.title}: {self.message[:20]}..."

    def save(self, *args, **kwargs):
        if self.highlighted:
            # If the current news has been marked as highlighted, find any other highlighted news and disable its
            # highlight
            existing_highlighted_news_qs = self._meta.model.objects.filter(highlighted=True)
            if self.id:
                existing_highlighted_news_qs = existing_highlighted_news_qs.exclude(id=self.id)
            existing_highlighted_news_qs.update(highlighted=False)

        super().save(*args, **kwargs)


class NewsComment(CommonInfo):
    news = models.ForeignKey(News, on_delete=models.CASCADE)
    comment = models.TextField(max_length=10000)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comment"
        default_related_name = "comments"
        ordering = ("id",)

    def __str__(self):
        return f'"{self.comment[:20]}" on {self.news.title}'
