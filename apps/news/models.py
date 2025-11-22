from ambient_toolbox.models import CommonInfo
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.mixins import FullCleanOnSaveMixin


class News(FullCleanOnSaveMixin, CommonInfo):
    class TypeChoices(models.IntegerChoices):
        ROOM_CREATED = 1, _("Room created")
        TRANSACTION_CREATED = 2, _("Transaction created")
        TRANSACTION_DELETED = 3, _("Transaction deleted")
        USER_ADDED = 4, _("User added")

    highlighted = models.BooleanField(default=False)
    title = models.CharField(max_length=100)
    message = models.TextField(max_length=10000)
    room = models.ForeignKey("room.Room", related_name="news", on_delete=models.DO_NOTHING)
    type = models.IntegerField(choices=TypeChoices.choices, null=True, blank=True)
    deeplink = models.CharField(max_length=512, blank=True)

    TYPE_ICONS = {
        TypeChoices.ROOM_CREATED: "🛠️",
        TypeChoices.TRANSACTION_CREATED: "💸",
        TypeChoices.TRANSACTION_DELETED: "🗑️",
        TypeChoices.USER_ADDED: "✨",
    }

    DEFAULT_HEADING_LABEL = _("News update")

    def _get_heading_label(self) -> str:
        if self.type:
            translated_label = self.get_type_display()
            if translated_label:
                return translated_label

        if self.title:
            return self.title

        return self.DEFAULT_HEADING_LABEL

    def _get_type_icon(self) -> str:
        return self.TYPE_ICONS.get(self.type, "")

    @property
    def heading(self) -> str:
        label = self._get_heading_label()
        icon = self._get_type_icon()
        initials = getattr(self.room, "capitalised_initials", "")

        if initials:
            prefix = f"{icon} {initials}" if icon else initials
            return f"{prefix}: {label}"

        if icon:
            return f"{icon} {label}"

        return label

    class Meta:
        verbose_name = "News"
        verbose_name_plural = "News"
        ordering = (
            "highlighted",
            "-id",
        )

    def __str__(self):
        heading = self.heading
        return f"{heading}: {self.message[:20]}..."

    def save(self, *args, **kwargs):
        if self.highlighted:
            # If the current news has been marked as highlighted, find any other highlighted news and disable its
            # highlight
            existing_highlighted_news_qs = self._meta.model.objects.filter(highlighted=True)
            if self.id:
                existing_highlighted_news_qs = existing_highlighted_news_qs.exclude(id=self.id)
            existing_highlighted_news_qs.update(highlighted=False)

        super().save(*args, **kwargs)
