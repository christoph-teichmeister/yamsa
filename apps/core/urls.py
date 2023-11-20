from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.BaseView.as_view(), name="core-base"),
    path("welcome/", views.WelcomePartialView.as_view(), name="core-welcome"),
    path("serviceworker.js", views.ServiceWorkerView.as_view(), name="core-serviceworker"),
    path("manifest.json", views.ManifestView.as_view(), name="core-manifest"),
    path("offline/", views.GetUserOfflineTemplateView.as_view(), name="core-offline"),
]
