from django.contrib import admin

from apps.room.models import UserConnectionToRoom


class UserConnectionToRoomInlineBase(admin.TabularInline):
    model = UserConnectionToRoom
    extra = 0
    readonly_fields = ("created_at", "created_by", "lastmodified_at", "lastmodified_by")
