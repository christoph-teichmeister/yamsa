import pytest

from apps.room.models import Room


@pytest.mark.django_db
class TestRoomQuerySetWithoutMembers:
    def test_returns_room_with_no_users(self, db):
        from apps.room.tests.factories import RoomFactory

        empty_room = RoomFactory()
        assert not empty_room.users.exists()

        qs = Room.objects.filter_without_members()
        assert qs.filter(pk=empty_room.pk).exists()

    def test_excludes_room_with_users(self, room):
        assert room.users.exists()

        qs = Room.objects.filter_without_members()
        assert not qs.filter(pk=room.pk).exists()

    def test_mixed_rooms_only_returns_empty_ones(self, room, db):
        from apps.room.tests.factories import RoomFactory

        empty_room = RoomFactory()

        qs = Room.objects.filter_without_members()
        pks = list(qs.values_list("pk", flat=True))

        assert empty_room.pk in pks
        assert room.pk not in pks
