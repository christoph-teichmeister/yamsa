from django.urls import path

from apps.news import views
from apps.room.urls import build_room_specific_paths

app_name = "news"

urlpatterns = [
    build_room_specific_paths(
        [
            path("", views.NewsListView.as_view(), name="list"),
            path("feed/", views.NewsFeedChunkView.as_view(), name="feed"),
        ]
    ),
]
