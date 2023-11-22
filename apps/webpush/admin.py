from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.webpush.models import WebpushInformation


@register(WebpushInformation)
class WebPushInformationAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "browser", "user", "created_at")
    list_filter = ("user",)
    search_fields = ("user",)
    fieldsets = (
        (
            None,
            {"fields": ("user", "endpoint", "browser", "user_agent", "auth", "p256dh")},
        ),
    )
    readonly_fields = ("user", "endpoint", "browser", "user_agent", "auth", "p256dh")
