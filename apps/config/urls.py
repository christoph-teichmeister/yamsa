from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

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
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

if "django_browser_reload" in settings.INSTALLED_APPS:
    urlpatterns.append(
        path("__reload__/", include("django_browser_reload.urls")),
    )
