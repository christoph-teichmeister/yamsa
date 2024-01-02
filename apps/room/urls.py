from django.urls import path, include

from apps.room import views


def build_room_specific_paths(list_of_url_paths: list):
    return path("<str:room_slug>/", include(list_of_url_paths))


app_name = "room"
urlpatterns = [
    path("list/", views.RoomListView.as_view(), name="list"),
    path("create/", views.RoomCreateView.as_view(), name="create"),
    path(
        "htmx/checked-clipboard",
        views.CheckedClipboardHTMXView.as_view(),
        name="htmx-checked-clipboard",
    ),
    build_room_specific_paths(
        [
            path("dashboard", views.RoomDashboardView.as_view(), name="dashboard"),
            path("detail", views.RoomDetailView.as_view(), name="detail"),
            path("edit", views.RoomEditView.as_view(), name="edit"),
        ]
    ),
]
