from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from apps.webpush import views

urlpatterns = [
    path("save/", csrf_exempt(views.WebPushSaveView.as_view()), name="webpush-save"),
]
