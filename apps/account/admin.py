from django.contrib import admin
from django.contrib.admin import register

from apps.account.models import User
from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.room.admin import UserConnectionToRoomInline
from apps.transaction.admin import TransactionPaidByInline


@register(User)
class UserAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("name", "email", "is_guest")
    list_filter = ("is_guest",)
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("email", "password", "is_guest")}),
        (
            "Personal Information",
            {
                "fields": ("name",),
            },
        ),
        (
            "Permissions",
            {"fields": (("is_superuser", "is_staff"), "groups", "user_permissions")},
        ),
    )
    extra_fields_for_fieldset = ("last_login",)
    inlines = (
        UserConnectionToRoomInline,
        TransactionPaidByInline,
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        readonly_fields += ("last_login",)

        return readonly_fields
