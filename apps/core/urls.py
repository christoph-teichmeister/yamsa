from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from apps.core import views

urlpatterns = [
    path("", views.BaseView.as_view(), name="core-base"),
    path("welcome/", views.WelcomePartialView.as_view(), name="core-welcome"),
    # path("webpush/save/", views.save_info, name="core-webpush-register"),
    path("webpush/save/", csrf_exempt(views.WebPushSaveView.as_view()), name="core-webpush-register"),
    path("offline/", views.GetUserOfflineTemplateView.as_view(), name="core-offline"),
    path("serviceworker.js", views.ServiceWorkerView.as_view(), name="core-serviceworker"),
    path("manifest.json", views.ManifestView.as_view(), name="core-manifest"),
]
