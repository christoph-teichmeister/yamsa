from django.db import models


class Currency(models.Model):
    name = models.CharField(max_length=200)
    sign = models.CharField(max_length=10)
    code = models.CharField(max_length=5)

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.code.upper()} ({self.sign})"
