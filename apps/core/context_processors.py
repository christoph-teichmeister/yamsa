from django.conf import settings


def core_context(request):
    return {
        "core": {
            # Calculated info
            "DEBUG": settings.DEBUG,
            "PROJECT_BASE_URL": settings.PROJECT_BASE_URL,
            "DJANGO_ADMIN_SUB_URL": settings.DJANGO_ADMIN_SUB_URL,
        },
    }
