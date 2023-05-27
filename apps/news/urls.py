from django.urls import path

from apps.news import views

urlpatterns = [
    path(
        "htmx/opened-news/<int:pk>",
        views.OpenedNewsHTMXView.as_view(),
        name="htmx-opened-news",
    ),
    path(
        "htmx/newscomment/create/",
        views.NewsCommentCreateHTMXView.as_view(),
        name="htmx-newscomment-create",
    ),
    path(
        "htmx/closed-news/<int:pk>",
        views.ClosedNewsHTMXView.as_view(),
        name="htmx-closed-news",
    ),
]
