import http

import pytest
from django.urls import reverse

from apps.account.tests.test_utils import contains_attribute
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestRoomDetailView:
    def test_the_sheet_starts_in_reading_mode(self, authenticated_client, room):
        response = authenticated_client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        # Server and client have to agree on the starting state, or the fields flash unlocked
        # until the bundle runs.
        assert contains_attribute(content, "data-sheet-mode", "reading")
        assert contains_attribute(content, "id", "edit-room-button")
        assert "readonly" in content

    def test_it_shows_the_rooms_own_values(self, authenticated_client, room):
        content = authenticated_client.get(reverse("room:detail", kwargs={"room_slug": room.slug})).content.decode()

        assert room.name in content
        assert str(Room.StatusChoices.OPEN.label) in content
        assert "Closing readiness" in content

    def test_an_open_room_without_debts_offers_to_close(self, authenticated_client, room):
        content = authenticated_client.get(reverse("room:detail", kwargs={"room_slug": room.slug})).content.decode()

        assert contains_attribute(content, "id", "close-room-button")
        assert not contains_attribute(content, "id", "force-close-dialog")

    def test_a_closed_room_offers_reopening_and_no_edit_mode(self, authenticated_client, closed_room):
        content = authenticated_client.get(
            reverse("room:detail", kwargs={"room_slug": closed_room.slug})
        ).content.decode()

        assert contains_attribute(content, "id", "reopen-room-button")
        # Nothing on a closed room is editable, so it offers no edit mode at all.
        assert not contains_attribute(content, "id", "edit-room-button")
        assert str(Room.StatusChoices.CLOSED.label) in content
