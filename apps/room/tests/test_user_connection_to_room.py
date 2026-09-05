import importlib

import pytest
from django.apps import apps as django_apps
from django.core.exceptions import ValidationError

from apps.room.models import UserConnectionToRoom

pytestmark = pytest.mark.django_db

deduplicate_user_connections = importlib.import_module(
    "apps.room.migrations.0010_deduplicate_user_connections"
).deduplicate_user_connections


class TestUniqueUserConnectionPerRoom:
    def test_a_second_connection_for_the_same_user_and_room_is_rejected(self, room, user):
        assert UserConnectionToRoom.objects.filter(user=user, room=room).count() == 1

        with pytest.raises(ValidationError):
            UserConnectionToRoom.objects.create(user=user, room=room)

    def test_the_same_user_can_still_join_several_rooms(self, room, closed_room, user):
        assert UserConnectionToRoom.objects.filter(user=user).count() == 2

    def test_two_users_can_share_a_room(self, room, user, guest_user):
        assert UserConnectionToRoom.objects.filter(room=room).count() == 2


class TestDeduplicateUserConnectionsMigration:
    def test_clean_data_is_left_untouched(self, room, closed_room, user, guest_user):
        connection_ids = set(UserConnectionToRoom.objects.values_list("id", flat=True))

        deduplicate_user_connections(django_apps, None)

        assert set(UserConnectionToRoom.objects.values_list("id", flat=True)) == connection_ids
