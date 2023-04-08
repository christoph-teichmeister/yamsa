from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.moneyflow.models import MoneyFlow


@register(MoneyFlow)
class MoneyFlowAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("user", "room")}),
        (
            "Money",
            {"fields": ("outgoing", "incoming")},
        ),
    )
