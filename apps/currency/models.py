from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.mixins import FullCleanOnSaveMixin


class Currency(FullCleanOnSaveMixin, models.Model):
    name = models.CharField(max_length=200)
    sign = models.CharField(max_length=10)
    code = models.CharField(max_length=5)

    class Meta:
        verbose_name = _("Currency")
        verbose_name_plural = _("Currencies")

    def __str__(self):
        return f"{self.code.upper()} ({self.sign})"
