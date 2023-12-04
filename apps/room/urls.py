from django.urls import path, include

from apps.room import views


def build_room_specific_paths(list_of_url_paths: list):
    return path("<str:room_slug>/", include(list_of_url_paths))


urlpatterns = [
    path("list/", views.RoomListView.as_view(), name="room-list"),
    path("create/", views.RoomCreateView.as_view(), name="room-create"),
    path(
        "htmx/checked-clipboard",
        views.CheckedClipboardHTMXView.as_view(),
        name="htmx-checked-clipboard",
    ),
    build_room_specific_paths(
        [
            path("dashboard", views.RoomDashboardView.as_view(), name="room-dashboard"),
            path("detail", views.RoomDetailView.as_view(), name="room-detail"),
            path("close", views.RoomCloseView.as_view(), name="room-close"),
        ]
    ),
]
