from django.conf import settings
from pywebpush import WebPushException, webpush

from apps.account.models import User
from apps.webpush.dataclasses import NotificationPayload
from apps.webpush.models import WebPushInformation


class NotificationSendService:
    def send_notification_to_user(self, user: User, payload: NotificationPayload, ttl: int = 0):
        if not user.is_superuser:
            return

        # Get all the web_push_info of the user
        for web_push_info in user.webpush_infos.all():
            self._send_notification(web_push_info, payload, ttl)

    @staticmethod
    def _send_notification(web_push_info: WebPushInformation, payload: NotificationPayload, ttl: int):
        try:
            return webpush(
                subscription_info={
                    "endpoint": web_push_info.endpoint,
                    "keys": {"p256dh": web_push_info.p256dh, "auth": web_push_info.auth},
                },
                data=payload.format_for_webpush(),
                ttl=ttl,
                **NotificationSendService._get_vapid_data(),
            )
        except WebPushException as e:
            # If the subscription has expired, delete it.
            if e.response.status_code == 410:
                web_push_info.delete()
            else:
                raise e

    @staticmethod
    def _get_vapid_data():
        vapid_data = {}

        webpush_settings = getattr(settings, "WEBPUSH_SETTINGS", {})

        # Vapid keys are optional, and mandatory only for Chrome.
        # If Vapid key is provided, include vapid key and claims
        if vapid_private_key := webpush_settings.get("VAPID_PRIVATE_KEY"):
            vapid_data = {
                "vapid_private_key": vapid_private_key,
                "vapid_claims": {"sub": f"mailto:{webpush_settings.get('VAPID_ADMIN_EMAIL')}"},
            }

        return vapid_data