from django.contrib import admin

from apps.transaction.models import ChildTransaction


class ChildTransactionInline(admin.TabularInline):
    model = ChildTransaction
    extra = 0
    fields = ("value", "paid_for")
    readonly_fields = fields

    def has_delete_permission(self, request, obj=None):
        return False
