from django.contrib import admin
from django.contrib.admin import register

from apps.currency.models import Currency


@register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ("sign", "code", "name")
    search_fields = ("name", "code")
    fieldsets = (
        (
            None,
            {"fields": (("sign", "code", "name"),)},
        ),
    )
