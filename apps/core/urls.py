from django.urls import path

from apps.core import views

app_name = "core"
urlpatterns = [
    path("", views.BaseView.as_view(), name="base"),
    path("healthcheck/", views.HealthcheckView.as_view(), name="healthcheck"),
    path("manifest.json", views.ManifestView.as_view(), name="manifest"),
    path("maintenance/", views.MaintenanceView.as_view(), name="maintenance"),
    path("offline/", views.OfflineView.as_view(), name="offline"),
    path("serviceworker.js", views.ServiceWorkerView.as_view(), name="serviceworker"),
    path("welcome/", views.WelcomePartialView.as_view(), name="welcome"),
]
