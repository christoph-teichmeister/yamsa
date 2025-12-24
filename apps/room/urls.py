from django.urls import include, path

from apps.room import views
from apps.room.views.user_connection_to_room_create_view import UserConnectionToRoomCreateView


def build_room_specific_paths(list_of_url_paths: list):
    return path("<str:room_slug>/", include(list_of_url_paths))


app_name = "room"
urlpatterns = [
    path("list/", views.RoomListView.as_view(), name="list"),
    path("create/", views.RoomCreateView.as_view(), name="create"),
    path("share/<str:share_hash>/", views.RoomShareView.as_view(), name="share"),
    path(
        "htmx/checked-clipboard",
        views.CheckedClipboardHTMXView.as_view(),
        name="htmx-checked-clipboard",
    ),
    path(
        "htmx/suggested-guest-friend-toggle",
        views.SuggestedGuestFriendToggleHTMXView.as_view(),
        name="htmx-suggested-guest-friend-toggle",
    ),
    build_room_specific_paths(
        [
            path("dashboard", views.RoomDashboardView.as_view(), name="dashboard"),
            path("detail", views.RoomDetailView.as_view(), name="detail"),
            path("edit", views.RoomEditView.as_view(), name="edit"),
            path(
                "userconnectiontoroom/create",
                UserConnectionToRoomCreateView.as_view(),
                name="userconnectiontoroom-create",
            ),
        ]
    ),
]
