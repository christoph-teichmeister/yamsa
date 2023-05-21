from django.contrib import admin
from django.contrib.admin import register

from apps.debt.admin import DebtInline
from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Transaction


class TransactionPaidByInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fk_name = "paid_by"
    fields = ("description", "room", "value", "settled", "settled_at")
    readonly_fields = fields


@register(Transaction)
class TransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "room", "settled")
    list_filter = ("room__name", "settled")
    fieldsets = (
        (None, {"fields": ("room", "description", "value")}),
        (
            "People involved",
            {"fields": ("paid_by",)},
        ),
        (
            "Status",
            {"fields": ("settled", "settled_at")},
        ),
    )
    inlines = (DebtInline,)
