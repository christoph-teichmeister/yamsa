from django.urls import path

from apps.news import views

app_name = "news"
urlpatterns = [
    path("htmx/list", views.HTMXFeedListContentListView.as_view(), name="htmx-list"),
]
