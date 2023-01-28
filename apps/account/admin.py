from ai_django_core.admin.model_admins.mixins import CommonInfoAdminMixin
from django.contrib import admin
from django.contrib.admin import register

from apps.account.models import User


@register(User)
class UserAdmin(admin.ModelAdmin, CommonInfoAdminMixin):
    list_display = ("name", "email", "is_guest")
