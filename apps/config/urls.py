from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.templatetags.static import static as staticfiles_url
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=staticfiles_url("images/favicon.ico"), permanent=True)),
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
