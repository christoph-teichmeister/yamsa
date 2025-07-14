from django.contrib import admin
from django.contrib.admin import register
from django.contrib.admin.filters import SimpleListFilter

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.debt.models import Debt
from apps.room.models import Room


class OpenRoomFilter(SimpleListFilter):
    title = "Open Room"
    parameter_name = "open_room"

    def lookups(self, request, model_admin):
        return [(room.name, room.name) for room in Room.objects.filter(status=Room.StatusChoices.OPEN)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(room__name=self.value(), room__status=Room.StatusChoices.OPEN)
        return queryset


class ClosedRoomFilter(SimpleListFilter):
    title = "Closed Room"
    parameter_name = "closed_room"

    def lookups(self, request, model_admin):
        return [(room.name, room.name) for room in Room.objects.filter(status=Room.StatusChoices.CLOSED)]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(room__name=self.value(), room__status=Room.StatusChoices.CLOSED)
        return queryset


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
