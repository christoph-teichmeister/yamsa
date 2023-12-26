from django.conf import settings


def core_context(request):
    return {
        "core": {
            # Calculated info
            "IS_LOCALHOST": settings.IS_LOCALHOST,
            "PROJECT_BASE_URL": settings.PROJECT_BASE_URL,
            "DJANGO_ADMIN_SUB_URL": settings.DJANGO_ADMIN_SUB_URL,
        },
    }
