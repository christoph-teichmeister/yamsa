from django.contrib import admin
from django.contrib.admin import register

from apps.debt.admin import DebtInline
from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Transaction


class TransactionPaidByInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fk_name = "paid_by"
    fields = ("description", "room", "value")
    readonly_fields = fields


@register(Transaction)
class TransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "room", "paid_by")
    list_filter = ("room__name",)
    fieldsets = (
        (None, {"fields": ("room", "description", ("value", "currency"))}),
        (
            "People involved",
            {"fields": ("paid_by",)},
        ),
    )
    # inlines = (DebtInline,)
