from apps.room.models import Room


def room_context(request):
    base_context = {
        "ROOM_STATUS_OPEN": Room.StatusChoices.OPEN.value,
        "ROOM_STATUS_CLOSED": Room.StatusChoices.CLOSED.value,
    }

    room: Room = getattr(request, "room", None)

    if room is None:
        return base_context

    return {
        **base_context,
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
            "has_guests": room.has_guests,
            "open_debt_count": room.debts.filter(settled=False).count(),
            "can_be_closed": room.can_be_closed,
        },
    }
