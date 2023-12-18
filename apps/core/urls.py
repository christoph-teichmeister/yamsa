from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.BaseView.as_view(), name="core-base"),
    path("welcome/", views.WelcomePartialView.as_view(), name="core-welcome"),
    path("offline/", views.OfflineView.as_view(), name="core-offline"),
    path("serviceworker.js", views.ServiceWorkerView.as_view(), name="core-serviceworker"),
    path("manifest.json", views.ManifestView.as_view(), name="core-manifest"),
]
