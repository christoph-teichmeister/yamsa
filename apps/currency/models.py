from ai_django_core.models import CommonInfo
from django.db import models


class Currency(CommonInfo):
    name = models.CharField(max_length=200)
    sign = models.CharField(max_length=10)

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.sign}: {self.name}"