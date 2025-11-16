from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.debt.models import ReminderLog


@register(ReminderLog)
class ReminderLogAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("id", "__str__", "reminder_type", "recipients_summary", "created_at")
    list_filter = ("reminder_type",)
    search_fields = ("reminder_type",)
    readonly_fields = ("created_at", "lastmodified_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "reminder_type",
                    "recipients",
                )
            },
        ),
    )

    def recipients_summary(self, obj: ReminderLog) -> str:
        return f"{len(obj.recipients)} recipients"

    recipients_summary.short_description = "Recipients"
