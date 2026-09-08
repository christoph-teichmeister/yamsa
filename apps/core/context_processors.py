from django.conf import settings

from apps.core.pwa_constants import CACHED_AT_HEADER_NAME, PREFETCH_HEADER_NAME
from apps.core.services.pwa_scope_service import resolve_scope
from apps.core.toast_constants import TOAST_TYPE_CLASSES


def core_context(request):
    return {
        "core": {
            # Calculated info
            "DEBUG": settings.DEBUG,
            "BACKEND_URL": settings.BACKEND_URL,
            "ADMIN_URL": settings.ADMIN_URL,
            "LANGUAGES": settings.LANGUAGES,
            "PWA_SCOPE": resolve_scope(getattr(request, "user", None)),
            "PWA_CACHED_AT_HEADER": CACHED_AT_HEADER_NAME,
            "PWA_PREFETCH_HEADER": PREFETCH_HEADER_NAME,
        },
        "toast_classes": TOAST_TYPE_CLASSES,
    }
