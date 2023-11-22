from ambient_toolbox.models import CommonInfo
from django.conf import settings
from django.db import models

from apps.core.models.mixins import FullCleanOnSaveMixin


class WebpushInformation(FullCleanOnSaveMixin, CommonInfo):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="webpush_infos", on_delete=models.CASCADE)

    browser = models.CharField(max_length=100)
    user_agent = models.CharField(max_length=500, blank=True)
    endpoint = models.URLField(max_length=500)
    auth = models.CharField(max_length=100)
    p256dh = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Webpush Information"
        verbose_name_plural = "Webpush Informations"

    def __str__(self):
        return f"Webpush Information for {self.user}"
