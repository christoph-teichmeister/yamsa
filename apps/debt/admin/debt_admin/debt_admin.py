from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.debt.models import Debt

from .closed_room_filter import ClosedRoomFilter
from .open_room_filter import OpenRoomFilter


@register(Debt)
class DebtAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("id", "__str__", "debitor", "creditor", "settled", "settled_at", "value")
    search_fields = ("debitor__name", "creditor__name", "room__name")
    list_filter = ("settled", OpenRoomFilter, ClosedRoomFilter)
    fieldsets = (
        (
            None,
            {"fields": ("room", ("debitor", "creditor"), ("value", "currency"), ("settled", "settled_at"))},
        ),
    )
