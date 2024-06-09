from django.contrib import admin
from django.contrib.admin import register

from apps.debt.models import Debt


@register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ("id", "__str__", "debitor", "creditor", "settled", "settled_at", "value")
    search_fields = ("debitor__name", "creditor__name", "room__name")
    list_filter = ("settled", "room__name")
    fieldsets = (
        (
            None,
            {"fields": ("room", ("debitor", "creditor"), ("value", "currency"), ("settled", "settled_at"))},
        ),
    )
