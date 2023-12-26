from django.conf import settings


def core_context(request):
    return {
        "core": {
            # Calculated info
            "is_localhost": settings.IS_LOCALHOST,
        },
    }
