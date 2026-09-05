import pytest
from django.core.exceptions import ValidationError

from apps.room.models import UserConnectionToRoom

pytestmark = pytest.mark.django_db


class TestUniqueUserConnectionPerRoom:
    def test_a_second_connection_for_the_same_user_and_room_is_rejected(self, room, user):
        assert UserConnectionToRoom.objects.filter(user=user, room=room).count() == 1

        with pytest.raises(ValidationError):
            UserConnectionToRoom.objects.create(user=user, room=room)

    def test_the_same_user_can_still_join_several_rooms(self, room, closed_room, user):
        assert UserConnectionToRoom.objects.filter(user=user).count() == 2

    def test_two_users_can_share_a_room(self, room, user, guest_user):
        assert UserConnectionToRoom.objects.filter(room=room).count() == 2
