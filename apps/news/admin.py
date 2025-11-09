from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.news.models import News


@register(News)
class NewsAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("highlighted", "title", "message", "room", "deeplink")}),)
    list_display = ("__str__", "title", "message", "highlighted", "room", "deeplink")
    list_filter = ("room",)
