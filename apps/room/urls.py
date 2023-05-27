from django.urls import path

from apps.room import views

urlpatterns = [
    path("list", views.RoomListView.as_view(), name="room-list"),
    path("create/", views.RoomCreateView.as_view(), name="room-create"),
    path("detail/<str:slug>", views.RoomDetailView.as_view(), name="room-detail"),
    path("detail/<str:slug>", views.RoomDetailView.as_view(), name="room-detail"),
    path("htmx/checked-clipboard", views.CheckedClipboardHTMXView.as_view(), name="htmx-checked-clipboard"),
]
