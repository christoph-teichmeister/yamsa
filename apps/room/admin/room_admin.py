from django.contrib import admin
from django.contrib.admin import register

from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.room.models import Room


@register(Room)
class RoomAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("name", "status")
    list_filter = ("status",)
    search_fields = ("name",)
    fieldsets = ((None, {"fields": ("name", "status", "description")}),)

    def get_inlines(self, request, obj):
        from apps.room.admin import UserConnectionToRoomInline

        return super().get_inlines(request, obj) + (UserConnectionToRoomInline,)
