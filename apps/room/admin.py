from ai_django_core.admin.model_admins.mixins import CommonInfoAdminMixin
from django.contrib import admin
from django.contrib.admin import register

from apps.room.models import Room, UserConnectionToRoom


@register(Room)
class RoomAdmin(CommonInfoAdminMixin, admin.ModelAdmin):
    pass


@register(UserConnectionToRoom)
class UserTransactionsForRoomAdmin(admin.ModelAdmin):
    pass
