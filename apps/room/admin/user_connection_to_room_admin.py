from django.contrib import admin
from django.contrib.admin import register

from apps.room.models import UserConnectionToRoom


@register(UserConnectionToRoom)
class UserConnectionToRoomAdmin(admin.ModelAdmin):
    list_display = ("room", "user")
    search_fields = ("room__name", "user__name")
    fieldsets = (
        (
            None,
            {"fields": ("user", "room")},
        ),
    )


class UserConnectionToRoomInline(admin.TabularInline):
    model = UserConnectionToRoom
    extra = 0
