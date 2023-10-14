from django.contrib import admin
from django.contrib.admin import register

from apps.debt.models import NewDebt


@register(NewDebt)
class NewDebtAdmin(admin.ModelAdmin):
    list_display = ("id", "__str__", "debitor", "creditor", "settled", "value")
    search_fields = ("debitor__name", "creditor__name", "room__name")
    list_filter = ("settled", "room__name")
    fieldsets = (
        (
            None,
            {"fields": ("room", ("debitor", "creditor"), ("value", "currency"), ("settled", "settled_at"))},
        ),
    )


class NewDebtInline(admin.TabularInline):
    model = NewDebt
    extra = 0
    fields = ("__str__", "debitor", "settled", "settled_at")
    readonly_fields = fields
