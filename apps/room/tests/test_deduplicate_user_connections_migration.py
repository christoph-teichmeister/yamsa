import importlib

import pytest
from django.apps import apps as django_apps
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from apps.room.models import UserConnectionToRoom

pytestmark = pytest.mark.django_db(transaction=True)

MIGRATION = "0010_deduplicate_user_connections"
BEFORE = ("room", "0009_room_share_hash")
AFTER = ("room", "0011_userconnectiontoroom_unique_user_connection_per_room")

deduplicate_user_connections = importlib.import_module(f"apps.room.migrations.{MIGRATION}").deduplicate_user_connections


@pytest.fixture
def pre_constraint_state():
    """Roll the schema back to before the unique constraint, so duplicates can exist at all."""
    executor = MigrationExecutor(connection)
    executor.migrate([BEFORE])
    yield executor.loader.project_state([BEFORE]).apps
    executor.loader.build_graph()
    executor.migrate([AFTER])


def create_connection(model, *, user, room, user_has_seen_this_room=False):
    return model.objects.create(
        user_id=user.id,
        room_id=room.id,
        user_has_seen_this_room=user_has_seen_this_room,
    )


class TestDeduplicateUserConnectionsMigration:
    def test_clean_data_is_left_untouched(self, room, closed_room, user, guest_user):
        connection_ids = set(UserConnectionToRoom.objects.values_list("id", flat=True))

        deduplicate_user_connections(django_apps, None)

        assert set(UserConnectionToRoom.objects.values_list("id", flat=True)) == connection_ids

    def test_duplicates_collapse_onto_the_oldest_connection(self, pre_constraint_state, room, user):
        model = pre_constraint_state.get_model("room", "UserConnectionToRoom")
        original = model.objects.get(user_id=user.id, room_id=room.id)
        create_connection(model, user=user, room=room)
        create_connection(model, user=user, room=room)
        assert model.objects.filter(user_id=user.id, room_id=room.id).count() == 3

        deduplicate_user_connections(pre_constraint_state, None)

        remaining = model.objects.filter(user_id=user.id, room_id=room.id)
        assert [row.id for row in remaining] == [original.id]

    def test_a_seen_flag_on_a_duplicate_survives_the_merge(self, pre_constraint_state, room, user):
        model = pre_constraint_state.get_model("room", "UserConnectionToRoom")
        model.objects.filter(user_id=user.id, room_id=room.id).update(user_has_seen_this_room=False)
        create_connection(model, user=user, room=room, user_has_seen_this_room=True)
        assert model.objects.filter(user_id=user.id, room_id=room.id).count() == 2

        deduplicate_user_connections(pre_constraint_state, None)

        kept = model.objects.get(user_id=user.id, room_id=room.id)
        assert kept.user_has_seen_this_room is True

    def test_connections_of_other_pairs_are_untouched(self, pre_constraint_state, room, user, guest_user):
        model = pre_constraint_state.get_model("room", "UserConnectionToRoom")
        create_connection(model, user=user, room=room)

        deduplicate_user_connections(pre_constraint_state, None)

        assert model.objects.filter(user_id=guest_user.id, room_id=room.id).count() == 1
