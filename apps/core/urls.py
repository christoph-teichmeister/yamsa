from django.urls import path

from apps.core import views

urlpatterns = [
    path("", views.BaseView.as_view(), name="core-base"),
    path("welcome/", views.WelcomePartialView.as_view(), name="core-welcome"),
    # path("serviceworker.js", service_worker, name="serviceworker"),
    path("manifest.json", views.ManifestView.as_view(), name="core-manifest"),
    # path("offline/", offline, name="offline"),
]
