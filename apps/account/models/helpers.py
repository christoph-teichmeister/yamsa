from apps.room.models import UserConnectionToRoom


def get_has_seen_room(userconnectiontoroom_set, room_id: int) -> tuple[UserConnectionToRoom | None, bool]:
    connections = userconnectiontoroom_set.filter(room_id=room_id)
    first_connection = connections.first()
    has_seen = connections.filter(user_has_seen_this_room=True).exists()
    return first_connection, has_seen
