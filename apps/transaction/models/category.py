from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext_lazy as _lazy

from apps.core.models.mixins import FullCleanOnSaveMixin

from .constants import DEFAULT_CATEGORY_SLUG


class Category(FullCleanOnSaveMixin, CommonInfo):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    emoji = models.CharField(max_length=10)
    color = models.CharField(max_length=7, blank=True, null=True)

    order_index = models.PositiveIntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("order_index", "id")
        verbose_name = _lazy("Transaction Category")
        verbose_name_plural = _lazy("Transaction Categories")

    def __str__(self) -> str:
        return f"{self.emoji} {self.name}"

    @classmethod
    def get_default_category(cls):
        default = cls.objects.filter(slug=DEFAULT_CATEGORY_SLUG).first()
        if default:
            return default
        return cls.objects.filter(is_default=True).order_by("order_index").first()
