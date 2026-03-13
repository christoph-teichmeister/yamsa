from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.admin.child_transaction_inline import ChildTransactionInline
from apps.transaction.models import ParentTransaction


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
