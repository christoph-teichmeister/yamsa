import http
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from pytest_django.fixtures import Settings

from apps.account.tests.test_utils import build_image_bytes, contains_attribute
from apps.room.models import Room
from apps.room.room_seal import SEAL_ICONS

pytestmark = pytest.mark.django_db


def build_upload(file_name: str = "seal.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(file_name, build_image_bytes(), content_type="image/png")


class TestRoomSealIconUpdateView:
    def test_post_stores_the_chosen_icon_and_answers_with_the_sheet(
        self, authenticated_client: Client, room: Room
    ) -> None:
        chosen = next(icon for icon in SEAL_ICONS if icon != room.resolved_seal_icon)

        response = authenticated_client.post(
            reverse("room:seal-icon-update", kwargs={"room_slug": room.slug}),
            data={"seal_icon": chosen},
        )

        assert response.status_code == http.HTTPStatus.OK
        assert contains_attribute(response.content.decode(), "id", "room-sheet")
        room.refresh_from_db()
        assert room.seal_icon == chosen

    def test_choosing_an_icon_clears_a_previously_uploaded_image(
        self, tmp_path: Path, settings: Settings, authenticated_client: Client, room: Room
    ) -> None:
        settings.MEDIA_ROOT = str(tmp_path)
        room.seal_image = build_upload()
        room.save(update_fields=["seal_image"])

        authenticated_client.post(
            reverse("room:seal-icon-update", kwargs={"room_slug": room.slug}),
            data={"seal_icon": SEAL_ICONS[0]},
        )

        room.refresh_from_db()
        assert room.seal_icon == SEAL_ICONS[0]
        assert not room.seal_image

    def test_an_unknown_icon_is_rejected_and_keeps_the_dialog_open(
        self, authenticated_client: Client, room: Room
    ) -> None:
        response = authenticated_client.post(
            reverse("room:seal-icon-update", kwargs={"room_slug": room.slug}),
            data={"seal_icon": "not-a-real-icon"},
        )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        dialog_tag = content[content.index("<dialog") : content.index(">", content.index("<dialog"))]
        assert "open" in dialog_tag
        room.refresh_from_db()
        assert room.seal_icon != "not-a-real-icon"

    def test_post_closed_room_is_rejected(self, authenticated_client: Client, closed_room: Room) -> None:
        response = authenticated_client.post(
            reverse("room:seal-icon-update", kwargs={"room_slug": closed_room.slug}),
            data={"seal_icon": SEAL_ICONS[0]},
        )

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        closed_room.refresh_from_db()
        assert closed_room.seal_icon == ""
