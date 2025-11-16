from django.contrib import admin
from django.contrib.admin import register
from django.contrib.admin.filters import SimpleListFilter

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.debt.models import Debt, ReminderLog
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


@register(ReminderLog)
class ReminderLogAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("id", "__str__", "reminder_type", "recipients_summary", "created_at")
    list_filter = ("reminder_type",)
    search_fields = ("reminder_type",)
    readonly_fields = ("created_at", "lastmodified_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "reminder_type",
                    "recipients",
                )
            },
        ),
    )

    def recipients_summary(self, obj: ReminderLog) -> str:
        return f"{len(obj.recipients)} recipients"

    recipients_summary.short_description = "Recipients"
