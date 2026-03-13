from django.contrib import admin

from apps.transaction.models import ParentTransaction


class ParentTransactionPaidByInline(admin.TabularInline):
    model = ParentTransaction
    extra = 0
    fk_name = "paid_by"
    fields = ("description", "room", "value")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
