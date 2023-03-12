from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Transaction


@register(Transaction)
class TransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("room", "description", "value")}),
        (
            "People involved",
            {"fields": ("paid_for", "paid_by")},
        ),
        (
            "Status",
            {"fields": ("settled", "settled_at")},
        ),
    )
