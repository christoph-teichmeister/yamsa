from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.debt.services.debt_optimise_service import DebtOptimiseService
from apps.room.models import Room


@admin.action(description="Optimise debts of selected Rooms")
def optimise_debts_for_room(modeladmin, request, queryset):  # pragma: no cover
    for room in queryset:
        DebtOptimiseService.process(room_id=room.id)


@register(Room)
class RoomAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    actions = (optimise_debts_for_room,)
    list_display = ("name", "status")
    list_filter = ("status",)
    search_fields = ("name",)
    readonly_fields = ("slug",)
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("name", "slug"),
                    "status",
                    "preferred_currency",
                    "description",
                )
            },
        ),
    )

    def get_inlines(self, request, obj):
        from apps.room.admin.user_connection_to_room_admin import UserConnectionToRoomForRoomAdminInline

        return *super().get_inlines(request, obj), UserConnectionToRoomForRoomAdminInline
