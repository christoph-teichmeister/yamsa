from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.admin.child_transaction_inline import ChildTransactionInline
from apps.transaction.models import ParentTransaction

DESCRIPTION_PREVIEW_LENGTH = 40


@register(ParentTransaction)
class ParentTransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "shortened_description", "room", "paid_by")
    list_filter = ("room__name",)
    fieldsets = ((None, {"fields": (("room", "currency", "paid_by", "paid_at"), "description")}),)
    inlines = (ChildTransactionInline,)

    @staticmethod
    def shortened_description(obj: ParentTransaction) -> str:
        description = obj.description or ""
        if len(description) > DESCRIPTION_PREVIEW_LENGTH:
            return f"{description[:DESCRIPTION_PREVIEW_LENGTH]}..."
        return description
