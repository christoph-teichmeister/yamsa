"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

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
