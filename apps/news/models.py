from ai_django_core.models import CommonInfo
from django.db import models


class News(CommonInfo):
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=10000)

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = ("-id",)

    def __str__(self):
        return f"{self.title}: {self.message[:20]}..."
