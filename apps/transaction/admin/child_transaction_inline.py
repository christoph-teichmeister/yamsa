from django.contrib import admin
from django.db.models import Model
from django.http import HttpRequest

from apps.transaction.models import ChildTransaction


class ChildTransactionInline(admin.TabularInline):
    model = ChildTransaction
    extra = 0
    fields = ("value", "paid_for")
    readonly_fields = fields

    def has_delete_permission(self, request: HttpRequest, obj: Model | None = None):
        return False
