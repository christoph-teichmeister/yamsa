from django.urls import path

from apps.webpush import views

app_name = "webpush"
urlpatterns = [
    path("save/", views.WebPushSaveView.as_view(), name="save"),
]
