from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.moneyflow.models import MoneyFlow, MoneyFlowLog


class MoneyFlowLogInline(admin.TabularInline):
    model = MoneyFlowLog
    extra = 0

    fields = ("log_message",)
    readonly_fields = fields


@register(MoneyFlow)
class MoneyFlowAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "user", "room")
    list_filter = ("room__name",)
    fieldsets = (
        (None, {"fields": ("user", "room")}),
        (
            "Money",
            {"fields": ("outgoing", "incoming")},
        ),
    )
    inlines = (MoneyFlowLogInline,)


@register(MoneyFlowLog)
class MoneyFlowLogAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    fieldsets = ((None, {"fields": ("money_flow", "log_message")}),)
