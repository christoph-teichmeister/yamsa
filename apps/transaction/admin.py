from ai_django_core.admin.model_admins.mixins import CommonInfoAdminMixin
from django.contrib import admin
from django.contrib.admin import register

from apps.transaction.models import Transaction


@register(Transaction)
class TransactionAdmin(admin.ModelAdmin, CommonInfoAdminMixin):
    pass
