from django.urls import path

from apps.news import views

app_name = "news"

urlpatterns = [
    path("", views.NewsListView.as_view(), name="list"),
    path("feed/", views.NewsFeedChunkView.as_view(), name="feed"),
]
