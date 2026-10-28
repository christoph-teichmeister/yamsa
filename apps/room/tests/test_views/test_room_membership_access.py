import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.factories import UserFactory
from apps.room.models import Room

pytestmark = pytest.mark.django_db

# The dashboard and detail pages are intentionally public: they render the guest login picker.
# (url name, method) of every other room-scoped view; these must be closed to non-members.
PROTECTED = [
    ("room:edit", "post"),
    ("room:status", "post"),
    ("room:delete", "post"),
    ("room:seal-icon-update", "post"),
    ("room:seal-image-update", "post"),
    ("room:seal-reset", "post"),
    ("room:userconnectiontoroom-create", "get"),
    ("account:list", "get"),
    ("account:guest-create", "get"),
    ("account:guest-create", "post"),
]


def _call(client: Client, name: str, method: str, room: Room) -> object:
    url = reverse(name, kwargs={"room_slug": room.slug})
    return getattr(client, method)(url, data={"name": "x"} if method == "post" else None)


@pytest.mark.parametrize(("name", "method"), PROTECTED)
class TestRoomViewsRequireMembership:
    def test_anonymous_is_sent_to_login(self, client: Client, room: Room, name: str, method: str) -> None:
        response = _call(client, name, method, room)

        assert response.status_code == http.HTTPStatus.FOUND
        assert reverse("account:login") in response["Location"]

    def test_non_member_is_forbidden(self, client: Client, room: Room, name: str, method: str) -> None:
        client.force_login(UserFactory())

        assert _call(client, name, method, room).status_code == http.HTTPStatus.FORBIDDEN

    def test_member_is_let_in(
        self, authenticated_client: Client, room: Room, closed_room: Room, name: str, method: str
    ) -> None:
        # An open room refuses deletion with 403, which would mask the membership check.
        response = _call(authenticated_client, name, method, closed_room if name == "room:delete" else room)

        assert response.status_code != http.HTTPStatus.FORBIDDEN
        assert response.status_code < http.HTTPStatus.INTERNAL_SERVER_ERROR
        assert reverse("account:login") not in response.get("Location", "")

    def test_superuser_is_let_in(
        self, client: Client, superuser: User, room: Room, closed_room: Room, name: str, method: str
    ) -> None:
        client.force_login(superuser)

        response = _call(client, name, method, closed_room if name == "room:delete" else room)

        assert response.status_code != http.HTTPStatus.FORBIDDEN
