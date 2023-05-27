from ai_django_core.models import CommonInfo
from django.db import models


class News(CommonInfo):
    highlighted = models.BooleanField(default=False)
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=10000)

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ("-id",)

    def __str__(self):
        return f"{self.title}: {self.message[:20]}..."

    def save(self, *args, **kwargs):
        if self.highlighted:
            # If the current news has been marked as highlighted, find any other highlighted news and disable its
            # highlight
            existing_highlighted_news_qs = self._meta.model.objects.filter(
                highlighted=True
            )
            if self.id:
                existing_highlighted_news_qs = existing_highlighted_news_qs.exclude(
                    id=self.id
                )
            existing_highlighted_news_qs.update(highlighted=False)

        super().save(*args, **kwargs)
