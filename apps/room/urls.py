from django.urls import path

from apps.room import views

urlpatterns = [
    path("rooms", views.RoomView.as_view(), name="room-room-list"),
]
