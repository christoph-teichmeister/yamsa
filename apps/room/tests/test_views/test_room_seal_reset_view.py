import http
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from pytest_django.fixtures import Settings

from apps.account.tests.test_utils import build_image_bytes
from apps.room.models import Room
from apps.room.room_seal import SEAL_ICONS

pytestmark = pytest.mark.django_db


def build_upload(file_name: str = "seal.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(file_name, build_image_bytes(), content_type="image/png")


class TestRoomSealResetView:
    def test_post_clears_both_the_icon_and_the_image(
        self, tmp_path: Path, settings: Settings, authenticated_client: Client, room: Room
    ):
        settings.MEDIA_ROOT = str(tmp_path)
        room.seal_icon = SEAL_ICONS[0]
        room.seal_image = build_upload()
        room.save(update_fields=["seal_icon", "seal_image"])

        response = authenticated_client.post(reverse("room:seal-reset", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        room.refresh_from_db()
        assert room.seal_icon == ""
        assert not room.seal_image

    def test_post_closed_room_is_rejected(self, authenticated_client: Client, closed_room: Room):
        closed_room.seal_icon = SEAL_ICONS[0]
        closed_room.save(update_fields=["seal_icon"])

        response = authenticated_client.post(reverse("room:seal-reset", kwargs={"room_slug": closed_room.slug}))

        assert response.status_code == http.HTTPStatus.FORBIDDEN
        closed_room.refresh_from_db()
        assert closed_room.seal_icon == SEAL_ICONS[0]
