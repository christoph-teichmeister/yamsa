from django.conf import settings


def core_context(request):
    return {
        "core": {
            # Calculated info
            "DEBUG": settings.DEBUG,
            "BACKEND_URL": settings.BACKEND_URL,
            "ADMIN_URL": settings.ADMIN_URL,
        },
    }
