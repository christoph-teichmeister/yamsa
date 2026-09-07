import http

import pytest
from django.urls import reverse

from apps.account.tests.test_utils import contains_attribute
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestRoomDetailView:
    def test_the_fields_are_editable_straight_away(self, authenticated_client, room):
        response = authenticated_client.get(reverse("room:detail", kwargs={"room_slug": room.slug}))
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        # No edit mode: the sheet is editable wherever it is shown, and the action row after the
        # fields is what carries saving.
        assert "readonly" not in content
        assert contains_attribute(content, "id", "save-room-button")
        assert contains_attribute(content, "id", "discard-room-button")

    def test_it_shows_the_rooms_own_values(self, authenticated_client, room):
        content = authenticated_client.get(reverse("room:detail", kwargs={"room_slug": room.slug})).content.decode()

        assert room.name in content
        assert str(Room.StatusChoices.OPEN.label) in content
        assert "Closing readiness" in content

    def test_an_open_room_without_debts_offers_to_close(self, authenticated_client, room):
        content = authenticated_client.get(reverse("room:detail", kwargs={"room_slug": room.slug})).content.decode()

        assert contains_attribute(content, "id", "close-room-button")
        assert not contains_attribute(content, "id", "force-close-dialog")

    def test_a_closed_room_offers_reopening_and_nothing_to_save(self, authenticated_client, closed_room):
        content = authenticated_client.get(
            reverse("room:detail", kwargs={"room_slug": closed_room.slug})
        ).content.decode()

        assert contains_attribute(content, "id", "reopen-room-button")
        # Nothing on a closed room can be edited, so its fields are inert and the actions stay out.
        assert not contains_attribute(content, "id", "save-room-button")
        assert "disabled" in content
        assert str(Room.StatusChoices.CLOSED.label) in content
