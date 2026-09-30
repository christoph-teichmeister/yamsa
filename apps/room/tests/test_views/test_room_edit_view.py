import http

import pytest
from django.test import Client
from django.urls import reverse

from apps.account.models import User
from apps.account.tests.test_utils import contains_attribute
from apps.room.models import Room

pytestmark = pytest.mark.django_db


class TestRoomEditView:
    def test_a_get_belongs_on_the_room(self, client: Client, user: User, room: Room):
        """There is no edit page left to land on — the room itself is editable."""
        client.force_login(user)

        response = client.get(reverse("room:edit", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.FOUND
        assert response["Location"] == reverse("room:detail", kwargs={"room_slug": room.slug})

    def test_an_htmx_save_answers_with_the_sheet_alone(self, authenticated_client: Client, room: Room):
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
        assert "<html" not in content

    def test_the_swapped_sheet_shows_the_saved_values(self, authenticated_client: Client, room: Room):
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

    def test_an_invalid_save_comes_back_with_the_error(self, authenticated_client: Client, room: Room):
        response = authenticated_client.post(
            reverse("room:edit", kwargs={"room_slug": room.slug}),
            data={"name": "", "description": "", "preferred_currency": room.preferred_currency.pk},
        )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        assert contains_attribute(content, "id", "room-sheet")
        assert "This field is required" in content
        room.refresh_from_db()
        assert room.name != ""

    def test_a_plain_save_redirects_to_the_room(self, client: Client, user: User, room: Room):
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

    def test_it_cannot_flip_the_status(self, authenticated_client: Client, room: Room):
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

    def test_it_records_who_saved(self, authenticated_client: Client, room: Room, user: User):
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

    def test_post_closed_room_is_rejected(self, authenticated_client: Client, closed_room: Room):
        original_name = closed_room.name

        response = authenticated_client.post(
            reverse("room:edit", kwargs={"room_slug": closed_room.slug}),
            data={
                "name": "Renamed while closed",
                "description": closed_room.description,
                "preferred_currency": closed_room.preferred_currency_id,
            },
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        closed_room.refresh_from_db()
        assert closed_room.name == original_name
