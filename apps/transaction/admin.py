from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Category, ChildTransaction, ParentTransaction


class ParentTransactionPaidByInline(admin.TabularInline):
    model = ParentTransaction
    extra = 0
    fk_name = "paid_by"
    fields = ("description", "room", "value")
    readonly_fields = fields


class ChildTransactionInline(admin.TabularInline):
    model = ChildTransaction
    extra = 0
    fields = ("value", "paid_for")
    readonly_fields = fields

    def has_delete_permission(self, request, obj=None):
        return False


@register(ParentTransaction)
class ParentTransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "shortened_description", "room", "paid_by")
    list_filter = ("room__name",)
    fieldsets = ((None, {"fields": (("room", "currency", "paid_by", "paid_at"), "description")}),)
    inlines = (ChildTransactionInline,)

    @staticmethod
    def shortened_description(obj: ParentTransaction) -> str:
        if len(obj.description) > 40:
            return f"{obj.description[:40]}..."
        return obj.description


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
