from django.contrib import admin
from django.contrib.admin import register

from apps.room.models import UserConnectionToRoom


@register(UserConnectionToRoom)
class UserConnectionToRoomAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "user_has_seen_this_room")
    search_fields = ("room__name", "user__name")
    list_filter = ("user_has_seen_this_room",)
    fieldsets = (
        (
            None,
            {"fields": ("user", "room", "user_has_seen_this_room")},
        ),
    )


class UserConnectionToRoomInline(admin.TabularInline):
    model = UserConnectionToRoom
    fk_name = "user"
    extra = 0
