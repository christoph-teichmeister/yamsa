from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Transaction, UserConnectionToTransaction


class UserConnectionToTransactionInline(admin.StackedInline):
    model = UserConnectionToTransaction
    extra = 0


class TransactionPaidByInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fk_name = "paid_by"
    fields = ("description", "room", "value", "settled", "settled_at")
    readonly_fields = fields


@register(Transaction)
class TransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
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
    inlines = (UserConnectionToTransactionInline,)


@register(UserConnectionToTransaction)
class UserConnectionToTransactionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "transaction", "user")
    search_fields = ("transaction__name", "user__name")
    fieldsets = (
        (
            None,
            {"fields": ("user", "transaction")},
        ),
    )
