from django.contrib import admin
from django.contrib.admin import register

from apps.account.models import User
from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.room.admin import UserConnectionToRoomInline
from apps.transaction.admin import ParentTransactionPaidByInline


@register(User)
class UserAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    list_display = ("name", "email", "is_guest", "is_superuser")
    list_filter = ("is_guest",)
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("password", "is_guest")}),
        ("Personal Information", {"fields": ("name", "paypal_me_username", "profile_picture")}),
        (
            "Permissions",
            {
                "fields": (
                    "wants_to_receive_webpush_notifications",
                    ("is_superuser", "is_staff"),
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "Email",
            {"fields": ("email", ("invitation_email_sent", "invitation_email_sent_at"))},
        ),
    )
    extra_fields_for_fieldset = ("last_login",)
    inlines = (
        UserConnectionToRoomInline,
        ParentTransactionPaidByInline,
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        readonly_fields += ("last_login",)

        return readonly_fields
