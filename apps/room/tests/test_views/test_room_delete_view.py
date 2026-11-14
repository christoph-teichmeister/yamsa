import http
from unittest import mock

import pytest
from django.test import Client
from django.urls import reverse

from apps.room.messages.commands.delete_room import DeleteRoom
from apps.room.models import Room

pytestmark = pytest.mark.django_db

DELETE_VIEW_MODULE = "apps.room.views.room_delete_view.handle_message"


class TestRoomHardDeleteView:
    def test_a_closed_room_dispatches_the_delete_command_and_the_client_leaves_it(
        self, authenticated_client: Client, closed_room: Room
    ) -> None:
        with mock.patch(DELETE_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(
                reverse("room:delete", kwargs={"room_slug": closed_room.slug}), {"confirm_name": closed_room.name}
            )

        assert response.status_code == http.HTTPStatus.FOUND
        assert response.url == reverse("core:welcome")

        handle_message.assert_called_once()
        message = handle_message.call_args[0][0]
        assert isinstance(message, DeleteRoom)
        assert message.Context.room == closed_room

    def test_a_closed_room_is_actually_gone_afterwards(self, authenticated_client: Client, closed_room: Room) -> None:
        room_id = closed_room.id

        response = authenticated_client.post(
            reverse("room:delete", kwargs={"room_slug": closed_room.slug}), {"confirm_name": closed_room.name}
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert not Room.objects.filter(id=room_id).exists()

    def test_an_open_room_is_refused(self, authenticated_client: Client, room: Room) -> None:
        with mock.patch(DELETE_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(
                reverse("room:delete", kwargs={"room_slug": room.slug}), {"confirm_name": room.name}
            )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        handle_message.assert_not_called()
        assert Room.objects.filter(id=room.id).exists()

    @pytest.mark.parametrize("typed", [None, "", "   ", "wrong name", "UPPER"])
    def test_a_missing_or_wrong_name_is_rejected_and_the_room_survives(
        self, authenticated_client: Client, closed_room: Room, typed: str | None
    ) -> None:
        data = {} if typed is None else {"confirm_name": typed}
        if typed == "UPPER":
            data = {"confirm_name": closed_room.name.swapcase()}

        with mock.patch(DELETE_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(reverse("room:delete", kwargs={"room_slug": closed_room.slug}), data)

        assert response.status_code == http.HTTPStatus.BAD_REQUEST
        handle_message.assert_not_called()
        assert Room.objects.filter(id=closed_room.id).exists()

    def test_surrounding_whitespace_around_the_right_name_is_accepted(
        self, authenticated_client: Client, closed_room: Room
    ) -> None:
        response = authenticated_client.post(
            reverse("room:delete", kwargs={"room_slug": closed_room.slug}), {"confirm_name": f"  {closed_room.name} "}
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert not Room.objects.filter(id=closed_room.id).exists()
