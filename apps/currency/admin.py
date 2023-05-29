from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.currency.models import Currency


@register(Currency)
class CurrencyAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("sign", "name")
    search_fields = ("name",)
    fieldsets = (
        (
            None,
            {"fields": (("sign", "name"),)},
        ),
    )
