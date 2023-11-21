from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from apps.web_push import views

urlpatterns = [
    # path("webpush/save/", views.save_info, name="core-webpush-register"),
    path("save/", csrf_exempt(views.WebPushSaveView.as_view()), name="webpush-save"),
]
