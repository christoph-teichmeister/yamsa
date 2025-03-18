from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.news.models import FeedItem


@register(FeedItem)
class FeedItemAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("text", "room")}),)
    list_display = ("text", "room", "action")
    list_filter = ("room", "action")
