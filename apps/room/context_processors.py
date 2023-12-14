from apps.room.models import Room


def room_context(request):
    room: Room = getattr(request, "room", None)

    if room is None:
        return {}

    return {
        "current_room": {
            "is_closed": room.status == room.StatusChoices.CLOSED,
            "is_open": room.status == room.StatusChoices.OPEN,
            "name": room.name,
            "slug": room.slug,
            "id": room.id,
            "preferred_currency": room.preferred_currency,
            "room_users": room.room_users,
        },
    }