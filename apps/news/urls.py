from django.urls import path

from apps.news import views

app_name = "news"

urlpatterns = [
    path("feed/", views.NewsFeedChunkView.as_view(), name="feed"),
]
