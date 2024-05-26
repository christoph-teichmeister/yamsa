from django.contrib import admin
from django.contrib.admin import register
from django.urls import reverse

from apps.account.models import User
from apps.core.admin import YamsaCommonInfoAdminMixin
from apps.mail.services.test_mail_service import TestEmailService
from apps.room.admin import UserConnectionToRoomInline
from apps.transaction.admin import ParentTransactionPaidByInline
from apps.webpush.utils import Notification


@admin.action(description="Send test notification to selected users")
def send_test_notification(modeladmin, request, queryset):  # pragma: no cover
    # TODO CT: Delete this once testing is done
    notification = Notification(
        payload=Notification.Payload(
            head="Test Notification",
            body="Click me to open your profile page",
        ),
    )
    for user in queryset:
        notification.payload.click_url = reverse(viewname="account:detail", kwargs={"pk": user.id})
        notification.send_to_user(user)


@admin.action(description="Send test email to selected users")
def send_test_email(modeladmin, request, queryset):  # pragma: no cover
    # TODO CT: Delete this once testing is done
    for user in queryset:
        service = TestEmailService(recipient=user)
        service.process()


@register(User)
class UserAdmin(YamsaCommonInfoAdminMixin, admin.ModelAdmin):
    actions = (send_test_notification, send_test_email)
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
