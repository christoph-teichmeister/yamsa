from django.contrib import admin
from django.contrib.admin import register

from apps.debt.models import Debt


@register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ("id", "__str__", "transaction", "user", "settled")
    search_fields = ("transaction__name", "user__name")
    list_filter = ("settled", "transaction__room__name")
    fieldsets = (
        (
            None,
            {"fields": ("user", "transaction", ("settled", "settled_at"))},
        ),
    )


class DebtInline(admin.TabularInline):
    model = Debt
    extra = 0
    fields = ("__str__", "user", "settled", "settled_at")
    readonly_fields = fields
