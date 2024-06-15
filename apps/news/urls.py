from django.urls import path

from apps.news import views

app_name = "news"
urlpatterns = [
    path(
        "htmx/opened-news/<int:pk>",
        views.OpenedNewsHTMXView.as_view(),
        name="htmx-opened-news",
    ),
]
