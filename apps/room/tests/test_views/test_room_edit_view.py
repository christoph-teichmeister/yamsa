import http

import pytest
from django.urls import reverse

from apps.account.tests.test_utils import contains_attribute
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestRoomEditView:
    def test_a_plain_get_carries_editing_without_the_bundle(self, client, user, room):
        client.force_login(user)

        response = client.get(reverse("room:edit", kwargs={"room_slug": room.slug}))
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        assert contains_attribute(content, "data-sheet-mode", "editing")
        assert contains_attribute(content, "id", "save-room-button")

    def test_an_htmx_save_answers_with_the_sheet_alone(self, authenticated_client, room):
        response = authenticated_client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={
                "name": "Renamed room",
                "description": "A new description",
                "preferred_currency": room.preferred_currency.pk,
            },
        )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        # The sheet alone, so the page shell and the scroll position survive the save.
        assert content.lstrip().startswith("<form")
        assert contains_attribute(content, "id", "room-sheet")
        assert contains_attribute(content, "data-sheet-mode", "reading")

    def test_the_swapped_sheet_shows_the_saved_values(self, authenticated_client, room):
        """request.room is loaded before the view runs, so the swap must not answer with it."""
        response = authenticated_client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={
                "name": "Renamed room",
                "description": "A new description",
                "preferred_currency": room.preferred_currency.pk,
            },
        )
        content = response.content.decode()

        assert "Renamed room" in content
        assert room.name not in content

    def test_an_invalid_save_comes_back_editing_with_the_error(self, authenticated_client, room):
        response = authenticated_client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={"name": "", "description": "", "preferred_currency": room.preferred_currency.pk},
        )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        assert contains_attribute(content, "data-sheet-mode", "editing")
        assert "This field is required" in content
        room.refresh_from_db()
        assert room.name != ""

    def test_a_plain_save_redirects_to_the_room(self, client, user, room):
        client.force_login(user)

        response = client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={
                "name": "Renamed room",
                "description": "A new description",
                "preferred_currency": room.preferred_currency.pk,
            },
        )

        assert response.status_code == http.HTTPStatus.FOUND
        assert response["Location"] == reverse("room:detail", kwargs={"room_slug": room.slug})
        room.refresh_from_db()
        assert room.name == "Renamed room"

    def test_it_cannot_flip_the_status(self, authenticated_client, room):
        authenticated_client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={
                "name": room.name,
                "description": room.description,
                "preferred_currency": room.preferred_currency.pk,
                "status": Room.StatusChoices.CLOSED,
            },
        )

        room.refresh_from_db()
        assert room.status == Room.StatusChoices.OPEN

    def test_it_records_who_saved(self, authenticated_client, room, user):
        authenticated_client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={
                "name": "Renamed room",
                "description": "A new description",
                "preferred_currency": room.preferred_currency.pk,
            },
        )

        room.refresh_from_db()
        assert room.lastmodified_by == user
