import pytest

from apps.account.handlers.commands.remove_user_from_room import handle_remove_user_from_room
from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.account.models import User
from apps.room.models import Room


@pytest.mark.django_db
class TestRemoveUserFromRoomHandler:
    def test_regular(self, room: Room, user: User, superuser: User):
        room.users.add(user)

        context = {
            "room": room,
            "user_to_be_removed": user,
            "user_requesting_removal": superuser,
        }
        result = handle_remove_user_from_room(context=RemoveUserFromRoom.Context(**context))

        assert isinstance(result, UserRemovedFromRoom)
        assert not user.rooms.filter(id=room.id).exists()
        assert result.Context.__dict__ == context
