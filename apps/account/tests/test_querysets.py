import pytest

from apps.account.models import User
from apps.room.models import UserConnectionToRoom
from apps.room.tests.factories import RoomFactory, UserConnectionToRoomFactory


@pytest.mark.django_db
class TestAnnotateUserHasSeenThisRoom:
    def test_returns_true_when_user_has_seen_room(self, user, room):
        UserConnectionToRoom.objects.filter(user=user, room=room).update(user_has_seen_this_room=True)

        qs = User.objects.filter(pk=user.pk).annotate_user_has_seen_this_room(room_id=room.pk)

        assert qs.count() == 1
        assert qs.first().user_has_seen_this_room is True

    def test_returns_false_when_user_has_not_seen_room(self, user, room):
        UserConnectionToRoom.objects.filter(user=user, room=room).update(user_has_seen_this_room=False)

        qs = User.objects.filter(pk=user.pk).annotate_user_has_seen_this_room(room_id=room.pk)

        assert qs.count() == 1
        assert qs.first().user_has_seen_this_room is False

    def test_excludes_users_not_in_room(self, user, guest_user, room):
        second_room = RoomFactory()
        UserConnectionToRoomFactory(user=guest_user, room=second_room)

        qs = User.objects.annotate_user_has_seen_this_room(room_id=second_room.pk)

        pks = list(qs.values_list("pk", flat=True))
        assert user.pk not in pks
        assert guest_user.pk in pks

    def test_regression_user_with_multiple_rooms_uses_correct_connection(self, user, room):
        # Regression: ensure annotation uses the connection for the requested room,
        # not another room the user belongs to.
        second_room = RoomFactory()
        UserConnectionToRoomFactory(user=user, room=second_room, user_has_seen_this_room=True)
        UserConnectionToRoom.objects.filter(user=user, room=room).update(user_has_seen_this_room=False)

        qs = User.objects.filter(pk=user.pk).annotate_user_has_seen_this_room(room_id=room.pk)

        assert qs.count() == 1
        assert qs.first().user_has_seen_this_room is False

    def test_regression_correct_room_seen_is_annotated_not_other(self, user, room):
        # Regression: user has seen a different room but not the requested one.
        second_room = RoomFactory()
        UserConnectionToRoomFactory(user=user, room=second_room, user_has_seen_this_room=False)
        UserConnectionToRoom.objects.filter(user=user, room=room).update(user_has_seen_this_room=True)

        qs = User.objects.filter(pk=user.pk).annotate_user_has_seen_this_room(room_id=second_room.pk)

        assert qs.count() == 1
        assert qs.first().user_has_seen_this_room is False
