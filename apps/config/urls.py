from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path


def trigger_error(_):
    """
    View that intentionally raises a ZeroDivisionError to test error monitoring.
    This is used for testing Sentry or other error tracking systems.
    """
    # This will cause a division by zero error
    _ = 1 / 0

    from django.http import HttpResponse

    # This code will never be reached due to the error above
    return HttpResponse("This page should never load properly")


urlpatterns = [
    path("", include("apps.core.urls")),
    # Django Admin, use {% url 'admin:index' %}
    path(f"{settings.ADMIN_URL}/", admin.site.urls),
    path("account/", include("apps.account.urls")),
    path("debt/", include("apps.debt.urls")),
    path("news/", include("apps.news.urls")),
    path("room/", include("apps.room.urls")),
    path("transaction/", include("apps.transaction.urls")),
    path("webpush/", include("apps.webpush.urls")),
    path("sentry/check/", trigger_error, name="sentry-test"),
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

if "django_browser_reload" in settings.INSTALLED_APPS:
    urlpatterns.append(
        path("__reload__/", include("django_browser_reload.urls")),
    )
