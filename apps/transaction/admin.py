from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import ChildTransaction, ParentTransaction


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
    fieldsets = ((None, {"fields": (("room", "currency", "paid_by"), "description")}),)
    inlines = (ChildTransactionInline,)

    @staticmethod
    def shortened_description(obj: ParentTransaction) -> str:
        if len(obj.description) > 40:
            return f"{obj.description[:40]}..."
        return obj.description
