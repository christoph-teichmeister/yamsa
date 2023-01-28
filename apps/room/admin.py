from ai_django_core.admin.model_admins.mixins import CommonInfoAdminMixin
from django.contrib import admin
from django.contrib.admin import register

from apps.room.models import Room, UserTransactionsForRoom


@register(Room)
class RoomAdmin(admin.ModelAdmin, CommonInfoAdminMixin):
    pass


@register(UserTransactionsForRoom)
class UserTransactionsForRoomAdmin(admin.ModelAdmin):
    pass
