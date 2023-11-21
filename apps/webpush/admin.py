from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.webpush.models import WebPushInformation


@register(WebPushInformation)
class WebPushInformationAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "user")
    search_fields = ("user",)
    fieldsets = (
        (
            None,
            {"fields": ("user", "endpoint", "browser", "user_agent", "auth", "p256dh")},
        ),
    )
    readonly_fields = ("user", "endpoint", "browser", "user_agent", "auth", "p256dh")
