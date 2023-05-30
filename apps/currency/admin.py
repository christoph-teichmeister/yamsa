from django.contrib import admin
from django.contrib.admin import register

from apps.currency.models import Currency


@register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("sign", "name")
    search_fields = ("name",)
    fieldsets = (
        (
            None,
            {"fields": (("sign", "name"),)},
        ),
    )
