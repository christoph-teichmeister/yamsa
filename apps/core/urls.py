from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.BaseView.as_view(), name="core-base"),
    path("healthcheck/", views.HealthcheckView.as_view(), name="core-healthcheck"),
    path("manifest.json", views.ManifestView.as_view(), name="core-manifest"),
    path("offline/", views.OfflineView.as_view(), name="core-offline"),
    path("serviceworker.js", views.ServiceWorkerView.as_view(), name="core-serviceworker"),
    path("welcome/", views.WelcomePartialView.as_view(), name="core-welcome"),
]
