import pytest
from django.test import Client
from django.urls import reverse

from apps.account.tests.factories import UserFactory
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestForeignRequestsChangeNothing:
    def test_anonymous_cannot_rename_the_room(self, client: Client, room: Room) -> None:
        name_before = room.name

        client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={"name": "Hijacked", "description": "", "preferred_currency": room.preferred_currency.pk},
        )

        room.refresh_from_db()
        assert room.name == name_before

    def test_non_member_cannot_delete_a_closed_room(self, client: Client, closed_room: Room) -> None:
        client.force_login(UserFactory())

        client.post(reverse("room:delete", kwargs={"room_slug": closed_room.slug}))

        assert Room.objects.filter(pk=closed_room.pk).exists()
