import logging

from django.conf import settings
from pywebpush import WebPushException, webpush

from apps.account.models import User
from apps.webpush.models import WebpushInformation

logger = logging.getLogger(__name__)


class NotificationSendService:
    def send_notification_to_user(self, user: User, payload: str, ttl: int = 0) -> list:
        # Get all the web_push_info of the user
        response_list = []
        for web_push_info in user.webpush_infos.all():
            response = self._send_notification(web_push_info, payload, ttl)
            if response is not None:
                response_list.append(response)

        return response_list

    @staticmethod
    def _send_notification(web_push_info: WebpushInformation, payload: str, ttl: int):
        try:
            return webpush(
                subscription_info={
                    "endpoint": web_push_info.endpoint,
                    "keys": {"p256dh": web_push_info.p256dh, "auth": web_push_info.auth},
                },
                data=payload,
                ttl=ttl,
                **NotificationSendService._get_vapid_data(),
            )
        except WebPushException as e:
            # If the subscription has expired, delete it.
            if getattr(e, "response", None) and e.response.status_code == 410:
                return web_push_info.delete()

            logger.debug(
                "webpush send failed for user %s (id=%s): %s",
                web_push_info.user,
                web_push_info.user_id,
                e,
                exc_info=True,
            )
            return None
        except Exception:
            logger.debug(
                "Unexpected error while sending webpush for user %s (id=%s)",
                web_push_info.user,
                web_push_info.user_id,
                exc_info=True,
            )
            return None

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
