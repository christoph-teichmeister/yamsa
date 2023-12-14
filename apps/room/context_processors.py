from apps.room.models import Room


def room_context(request):
    room: Room = getattr(request, "room", None)

    if room is None:
        return {}

    return {
        "current_room": {
            # Model fields
            "id": room.id,
            "slug": room.slug,
            "name": room.name,
            "description": room.description,
            "status": room.status,
            "preferred_currency": room.preferred_currency,
            "users": room.room_users,
            # Calculated info
            "is_closed": room.status == room.StatusChoices.CLOSED,
            "is_open": room.status == room.StatusChoices.OPEN,
        },
    }
