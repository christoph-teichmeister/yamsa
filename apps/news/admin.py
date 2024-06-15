from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.news.models import News


@register(News)
class NewsAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("title", "room")}),)
    list_display = ("__str__", "title", "room")
    list_filter = ("room",)
