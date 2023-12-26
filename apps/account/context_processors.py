from apps.room.models import Room


def user_context(request):
    user = request.user
    if not user.is_authenticated:
        return {}

    base_room_qs_for_list = user.room_qs_for_list

    room_qs_of_user = base_room_qs_for_list.filter(users=user)
    other_rooms_qs = base_room_qs_for_list.exclude(users=user)

    open_room_qs_for_list = room_qs_of_user.filter(status=Room.StatusChoices.OPEN)
    closed_room_qs_for_list = room_qs_of_user.filter(status=Room.StatusChoices.CLOSED)

    return {
        "current_user": {
            # Calculated info
            "open_room_qs_for_list": open_room_qs_for_list,
            "closed_room_qs_for_list": closed_room_qs_for_list,
            "other_rooms_qs_for_list": other_rooms_qs,
        },
    }
