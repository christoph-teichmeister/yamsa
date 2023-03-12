from django.urls import path

from apps.room import views

urlpatterns = [
    path("rooms", views.RoomListView.as_view(), name="room-list"),
    path("room/<int:pk>", views.RoomDetailView.as_view(), name="room-detail"),
]
