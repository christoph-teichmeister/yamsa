import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.tests.factories import UserFactory
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestClosedRoomResponse:
    """The mixin sits behind RoomMembershipRequiredMixin, whose plain 403 must not shadow its message."""

    def test_a_member_of_a_closed_room_gets_the_closed_room_message(
        self, authenticated_client: Client, closed_room: Room
    ) -> None:
        response = authenticated_client.post(reverse("transaction:create", kwargs={"room_slug": closed_room.slug}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert "This room is closed. No changes can be made." in response.content.decode()

    def test_a_non_member_gets_the_plain_forbidden_without_the_message(self, client: Client, closed_room: Room) -> None:
        client.force_login(UserFactory())

        response = client.post(reverse("transaction:create", kwargs={"room_slug": closed_room.slug}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        assert "This room is closed" not in response.content.decode()
