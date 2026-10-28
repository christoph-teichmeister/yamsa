import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest
from django.test import RequestFactory

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.models import Room, UserConnectionToRoom
from apps.room.services.request_room_service import assign_room_to_request

pytestmark = pytest.mark.django_db


class TestAssignRoomToRequest:
    def _request(self, user: object) -> HttpRequest:
        request = RequestFactory().get("/")
        request.user = user
        return request

    def test_anonymous_gets_the_room_and_no_connection_is_touched(self, room: Room) -> None:
        request = self._request(AnonymousUser())

        assign_room_to_request(request, room)

        assert request.room == room
        assert not UserConnectionToRoom.objects.filter(room=room, user_has_seen_this_room=True).exists()

    def test_non_member_creates_no_connection(self, room: Room) -> None:
        stranger = UserFactory()

        assign_room_to_request(self._request(stranger), room)

        assert not UserConnectionToRoom.objects.filter(user=stranger, room=room).exists()

    def test_superuser_who_is_not_a_member_creates_no_connection(self, room: Room, superuser: User) -> None:
        assign_room_to_request(self._request(superuser), room)

        assert not UserConnectionToRoom.objects.filter(user=superuser, room=room).exists()

    def test_member_marks_the_room_as_seen(self, room: Room, user: User) -> None:
        assign_room_to_request(self._request(user), room)

        assert UserConnectionToRoom.objects.get(user=user, room=room).user_has_seen_this_room
