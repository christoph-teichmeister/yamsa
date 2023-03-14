from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Transaction, UserConnectionToTransaction


@register(Transaction)
class TransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("room", "description", "value")}),
        (
            "People involved",
            {
                "fields": (
                    # "paid_for",
                    "paid_by",
                )
            },
        ),
        (
            "Status",
            {"fields": ("settled", "settled_at")},
        ),
    )


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


class UserConnectionToTransactionInline(admin.TabularInline):
    model = UserConnectionToTransaction
    extra = 0
