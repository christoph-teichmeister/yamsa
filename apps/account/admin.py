from django.contrib import admin
from django.contrib.admin import register

from apps.account.models import User
from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.room.admin import UserConnectionToRoomInline
from apps.transaction.admin import ParentTransactionPaidByInline
from apps.webpush.services import NotificationSendService


@admin.action(description="Send test notification to selected users")
def make_published(modeladmin, request, queryset):
    # TODO CT: Delete this once testing is done
    for user in queryset:
        notification_service = NotificationSendService()
        notification_service.send_notification_to_user(
            user=user,
            payload={
                "head": "Test Notification",
                "body": f"Die hier kam aus dem Admin von {request.user}",
                "icon": "http://localhost:8000/static/images/favicon.ico",
            },
            ttl=1000,
        )


@register(User)
class UserAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    actions = (make_published,)
    list_display = ("name", "email", "is_guest", "is_superuser")
    list_filter = ("is_guest",)
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("email", "password", "is_guest")}),
        (
            "Personal Information",
            {
                "fields": ("name", "paypal_me_username"),
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
        ParentTransactionPaidByInline,
    )

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        readonly_fields += ("last_login",)

        return readonly_fields
