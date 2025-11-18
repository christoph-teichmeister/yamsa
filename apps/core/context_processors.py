from django.conf import settings

from apps.core.toast_constants import TOAST_TYPE_CLASSES


def core_context(request):
    return {
        "core": {
            # Calculated info
            "DEBUG": settings.DEBUG,
            "BACKEND_URL": settings.BACKEND_URL,
            "ADMIN_URL": settings.ADMIN_URL,
        },
        "toast_classes": TOAST_TYPE_CLASSES,
    }
