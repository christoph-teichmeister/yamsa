import http
from unittest import mock

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.account.tests.test_utils import contains_attribute
from apps.debt.models import Debt
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room
from apps.room.tests.test_forms.test_room_status_form import create_open_debt

pytestmark = pytest.mark.django_db

STATUS_VIEW_MODULE = "apps.room.views.room_status_update_view.handle_message"


class TestRoomStatusUpdateView:
    def test_a_settled_room_closes_and_answers_with_the_sheet(self, authenticated_client, room):
        with mock.patch(STATUS_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(
                reverse("room:status", kwargs={"room_slug": room.slug}),
                data={"status": Room.StatusChoices.CLOSED},
            )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        assert contains_attribute(content, "id", "room-sheet")
        assert contains_attribute(content, "id", "reopen-room-button")
        room.refresh_from_db()
        assert room.status == Room.StatusChoices.CLOSED

        handle_message.assert_called_once()
        assert isinstance(handle_message.call_args[0][0], RoomStatusChanged)

    def test_open_debts_block_the_close_and_come_back_as_an_error(self, authenticated_client, room):
        create_open_debt(room)

        response = authenticated_client.post(
            reverse("room:status", kwargs={"room_slug": room.slug}),
            data={"status": Room.StatusChoices.CLOSED},
        )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        assert contains_attribute(content, "id", "room-status-error")
        assert "open debts" in content
        room.refresh_from_db()
        assert room.status == Room.StatusChoices.OPEN

    def test_the_force_flag_closes_the_room_and_settles_its_debts(self, authenticated_client, room):
        create_open_debt(room)

        with mock.patch(STATUS_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(
                reverse("room:status", kwargs={"room_slug": room.slug}),
                data={"status": Room.StatusChoices.CLOSED, "force_close": "true"},
            )

        assert response.status_code == http.HTTPStatus.OK
        room.refresh_from_db()
        assert room.status == Room.StatusChoices.CLOSED

        debt = Debt.objects.get(room=room)
        assert debt.settled
        assert debt.settled_at == timezone.localdate()
        handle_message.assert_called_once()

    def test_a_closed_room_reopens(self, authenticated_client, closed_room):
        with mock.patch(STATUS_VIEW_MODULE) as handle_message:
            response = authenticated_client.post(
                reverse("room:status", kwargs={"room_slug": closed_room.slug}),
                data={"status": Room.StatusChoices.OPEN},
            )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        # Reopening puts the fields and their action row back.
        assert contains_attribute(content, "id", "save-room-button")
        closed_room.refresh_from_db()
        assert closed_room.status == Room.StatusChoices.OPEN
        handle_message.assert_called_once()

    def test_the_rooms_own_fields_are_ignored(self, authenticated_client, room):
        """htmx posts the enclosing sheet along, and none of it may reach the room."""
        with mock.patch(STATUS_VIEW_MODULE):
            authenticated_client.post(
                reverse("room:status", kwargs={"room_slug": room.slug}),
                data={
                    "status": Room.StatusChoices.CLOSED,
                    "name": "Renamed by the status post",
                    "description": "Should not land either",
                },
            )

        room.refresh_from_db()
        assert room.name != "Renamed by the status post"
        assert room.status == Room.StatusChoices.CLOSED

    def test_a_post_that_repeats_the_status_fires_no_event(self, authenticated_client, room):
        with mock.patch(STATUS_VIEW_MODULE) as handle_message:
            authenticated_client.post(
                reverse("room:status", kwargs={"room_slug": room.slug}),
                data={"status": Room.StatusChoices.OPEN},
            )

        handle_message.assert_not_called()
