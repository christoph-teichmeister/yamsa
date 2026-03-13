from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Category


@register(Category)
class CategoryAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "emoji", "color", "order_index", "is_default")
    ordering = ("order_index", "id")
    list_filter = ("is_default",)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop("delete_selected", None)
        return actions

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_default:
            return False
        return super().has_delete_permission(request, obj)
