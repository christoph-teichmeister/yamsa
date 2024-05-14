from django.conf import settings
from django.urls import reverse
from django.utils.module_loading import import_string

Notification = import_string(settings.WEBPUSH_NOTIFICATION_CLASS)


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
