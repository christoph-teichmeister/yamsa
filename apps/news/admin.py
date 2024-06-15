from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.news.models import News, NewsComment


@register(NewsComment)
class NewsCommentAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("news", "comment")}),)
    list_display = ("__str__", "comment", "news")


class NewsCommentInline(admin.TabularInline):
    model = NewsComment
    extra = 0

    fields = ("comment", "created_by")


@register(News)
class NewsAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("title", "message", "room")}),)
    list_display = ("__str__", "title", "message", "room")
    list_filter = ("room",)
    inlines = (NewsCommentInline,)
