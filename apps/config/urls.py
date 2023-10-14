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
from django.contrib import admin
from django.urls import include, path, re_path

from apps.config.settings import DJANGO_ADMIN_SUB_URL
from apps.core.views import MaintenanceView

urlpatterns = (
    [
        path("", include("apps.core.urls")),
        path(f"{DJANGO_ADMIN_SUB_URL}/", admin.site.urls),
        path("account/", include("apps.account.urls")),
        path("debt/", include("apps.debt.urls")),
        path("news/", include("apps.news.urls")),
        path("room/", include("apps.room.urls")),
        path("transaction/", include("apps.transaction.urls")),
    ]
    if not settings.MAINTENANCE
    else [
        path(f"{DJANGO_ADMIN_SUB_URL}/", admin.site.urls),
        # Empty URLs
        path("", MaintenanceView.as_view(), name="core-maintenance"),
        # Any other URLs / wildcard
        re_path(r"^.*/$", MaintenanceView.as_view(), name="core-maintenance"),
    ]
)
