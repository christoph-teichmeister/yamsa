import pytest

from apps.room.models import Room


@pytest.mark.django_db
class TestRoomCanBeDeleted:
    def test_an_open_room_can_not_be_deleted(self, room):
        assert room.status == Room.StatusChoices.OPEN
        assert not room.can_be_deleted

    def test_a_closed_room_can_be_deleted(self, closed_room):
        assert closed_room.can_be_deleted
