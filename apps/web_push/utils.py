import json

from django.conf import settings
from django.urls import reverse
from pywebpush import WebPushException, webpush

from apps.web_push.models import WebPushInformation


def send_notification_to_user(user, payload, ttl=0):
    # Get all the web_push_info of the user
    for web_push_info in user.webpush_infos.all():
        _send_notification(web_push_info, payload, ttl)


# def send_notification_to_group(group_name, payload, ttl=0, exclude_user_id=None):
#     from .models import Group
#
#     web_push_infos = Group.objects.get(name=group_name).webweb_push_info.select_related("subscription")
#
#     # Exclude the current user from receiving notifications if they are part of the target group.
#     # This prevents users from receiving redundant notifications when they trigger an event themselves.
#     if exclude_user_id is not None:
#         web_push_infos = web_push_infos.exclude(user__id=exclude_user_id)
#
#     for web_push_info in web_push_infos:
#         _send_notification(web_push_info.subscription, payload, ttl)


def send_to_subscription(subscription, payload, ttl=0):
    return _send_notification(subscription, payload, ttl)


def _send_notification(web_push_info: WebPushInformation, payload, ttl):
    subscription_data = _process_subscription_info(web_push_info)
    vapid_data = {}

    webpush_settings = getattr(settings, "WEBPUSH_SETTINGS", {})
    vapid_private_key = webpush_settings.get("VAPID_PRIVATE_KEY")
    vapid_admin_email = webpush_settings.get("VAPID_ADMIN_EMAIL")

    # Vapid keys are optional, and mandatory only for Chrome.
    # If Vapid key is provided, include vapid key and claims
    if vapid_private_key:
        vapid_data = {
            "vapid_private_key": vapid_private_key,
            "vapid_claims": {"sub": "mailto:{}".format(vapid_admin_email)},
        }

    try:
        return webpush(subscription_info=subscription_data, data=payload, ttl=ttl, **vapid_data)
    except WebPushException as e:
        # If the subscription is expired, delete it.
        if e.response.status_code == 410:
            web_push_info.delete()
        else:
            # Its other type of exception!
            raise e


def _process_subscription_info(web_push_info: WebPushInformation):
    return {"endpoint": web_push_info.endpoint, "keys": {"p256dh": web_push_info.p256dh, "auth": web_push_info.auth}}


def get_templatetag_context(context):
    request = context["request"]
    vapid_public_key = getattr(settings, "WEBPUSH_SETTINGS", {}).get("VAPID_PUBLIC_KEY", "")

    data = {
        "group": context.get("webpush", {}).get("group"),
        "user": getattr(request, "user", None),
        "vapid_public_key": vapid_public_key,
        "webpush_save_url": reverse("save_webweb_push_info"),
    }

    return data


def send_user_notification(user, payload, ttl=0):
    if not user.is_superuser:
        return

    payload = json.dumps(payload)
    send_notification_to_user(user, payload, ttl)
