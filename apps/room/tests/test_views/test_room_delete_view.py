import http
from unittest import mock

import pytest
from django.urls import reverse

from apps.room.messages.commands.delete_room import DeleteRoom
from apps.room.models import Room

pytestmark = pytest.mark.django_db

DELETE_VIEW_MODULE = "apps.room.views.room_delete_view.handle_message"


class TestRoomHardDeleteView:
    def test_a_closed_room_dispatches_the_delete_command_and_the_client_leaves_it(
        self, authenticated_client, closed_room
    ):
        with mock.patch(DELETE_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(reverse("room:delete", kwargs={"room_slug": closed_room.slug}))

        assert response.status_code == http.HTTPStatus.FOUND
        assert response.url == reverse("core:welcome")

        handle_message.assert_called_once()
        message = handle_message.call_args[0][0]
        assert isinstance(message, DeleteRoom)
        assert message.Context.room == closed_room

    def test_a_closed_room_is_actually_gone_afterwards(self, authenticated_client, closed_room):
        room_id = closed_room.id

        response = authenticated_client.post(reverse("room:delete", kwargs={"room_slug": closed_room.slug}))

        assert response.status_code == http.HTTPStatus.FOUND
        assert not Room.objects.filter(id=room_id).exists()

    def test_an_open_room_is_refused(self, authenticated_client, room):
        with mock.patch(DELETE_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(reverse("room:delete", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        handle_message.assert_not_called()
        assert Room.objects.filter(id=room.id).exists()
