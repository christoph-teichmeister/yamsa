from django.conf import settings
from django.db import models


class PushInformation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="webpush_infos", on_delete=models.CASCADE)

    browser = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=500, blank=True)
    endpoint = models.URLField(max_length=500)
    auth = models.CharField(max_length=100)
    p256dh = models.CharField(max_length=100)

    class Meta:
        verbose_name = "PushInformation"
        verbose_name_plural = "PushInformations"
