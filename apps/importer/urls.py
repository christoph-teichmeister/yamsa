from django.urls import path

from apps.importer import views

app_name = "importer"
urlpatterns = [
    path("upload/", views.ImportUploadView.as_view(), name="upload"),
    path("preview/", views.ImportPreviewView.as_view(), name="preview"),
]
