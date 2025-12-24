from __future__ import annotations

from django.http import HttpRequest

from apps.room.models import Room


def assign_room_to_request(request: HttpRequest, room: Room) -> None:
    request.room = room

    if request.user.is_anonymous:
        return

    connection, has_seen_room = request.user.has_seen_room(room.id)

    request_user_is_superuser_and_does_not_belong_to_room = connection is None and request.user.is_superuser
    if request_user_is_superuser_and_does_not_belong_to_room:
        return

    if connection is None:
        return

    if not has_seen_room:
        connection.user_has_seen_this_room = True
        connection.save()
