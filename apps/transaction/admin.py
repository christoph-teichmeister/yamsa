from django.contrib import admin
from django.contrib.admin import register
from django.urls import resolve

from apps.account.models import User
from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.transaction.models import Transaction, ParentTransaction, ChildTransaction


class TransactionPaidByInline(admin.TabularInline):
    model = Transaction
    extra = 0
    fk_name = "paid_by"
    fields = ("description", "room", "value")
    readonly_fields = fields


@register(Transaction)
class TransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "description", "room", "paid_by")
    list_filter = ("room__name",)
    fieldsets = (
        (None, {"fields": ("room", "description", ("value", "currency"))}),
        (
            "People involved",
            {"fields": ("paid_by", "paid_for")},
        ),
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "paid_for":
            transaction = self.get_object(request, resolve(request.path).kwargs.get("object_id"))
            kwargs["queryset"] = User.objects.filter(room=transaction.room)
        return super().formfield_for_manytomany(db_field, request, **kwargs)


class ChildTransactionInline(admin.TabularInline):
    model = ChildTransaction
    extra = 0
    fields = ("value", "paid_for")
    readonly_fields = fields

    def has_delete_permission(self, request, obj=None):
        return False


@register(ParentTransaction)
class ParentTransactionAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("__str__", "shortened_description", "room", "paid_by")
    list_filter = ("room__name",)
    fieldsets = ((None, {"fields": (("room", "currency", "paid_by"), "description")}),)
    inlines = (ChildTransactionInline,)

    @staticmethod
    def shortened_description(obj: ParentTransaction) -> str:
        if len(obj.description) > 40:
            return f"{obj.description[:40]}..."
        return obj.description
