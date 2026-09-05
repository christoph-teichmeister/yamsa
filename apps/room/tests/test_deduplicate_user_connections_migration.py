import importlib

import pytest
from django.apps import apps as django_apps

from apps.room.models import UserConnectionToRoom

pytestmark = pytest.mark.django_db

deduplicate_user_connections = importlib.import_module(
    "apps.room.migrations.0010_deduplicate_user_connections"
).deduplicate_user_connections


class TestDeduplicateUserConnectionsMigration:
    def test_clean_data_is_left_untouched(self, room, closed_room, user, guest_user):
        connection_ids = set(UserConnectionToRoom.objects.values_list("id", flat=True))

        deduplicate_user_connections(django_apps, None)

        assert set(UserConnectionToRoom.objects.values_list("id", flat=True)) == connection_ids
