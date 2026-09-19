import http

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.account.tests.test_utils import build_image_bytes, contains_attribute
from apps.room.room_seal import SEAL_ICONS

pytestmark = pytest.mark.django_db


def build_upload(file_name: str = "seal.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(file_name, build_image_bytes(), content_type="image/png")


class TestRoomSealImageUpdateView:
    def test_post_stores_the_image_and_clears_any_chosen_icon(self, tmp_path, settings, authenticated_client, room):
        settings.MEDIA_ROOT = str(tmp_path)
        room.seal_icon = SEAL_ICONS[0]
        room.save(update_fields=["seal_icon"])

        response = authenticated_client.post(
            reverse("room:seal-image-update", kwargs={"room_slug": room.slug}),
            data={"seal_image": build_upload()},
        )

        assert response.status_code == http.HTTPStatus.OK
        assert contains_attribute(response.content.decode(), "id", "room-sheet")
        room.refresh_from_db()
        assert room.seal_image
        assert room.seal_icon == ""

    def test_post_of_an_invalid_file_keeps_the_dialog_open_with_the_error(
        self, tmp_path, settings, authenticated_client, room
    ):
        settings.MEDIA_ROOT = str(tmp_path)
        corrupted = SimpleUploadedFile("seal.bin", b"not-an-image", content_type="application/octet-stream")

        response = authenticated_client.post(
            reverse("room:seal-image-update", kwargs={"room_slug": room.slug}),
            data={"seal_image": corrupted},
        )
        content = response.content.decode()

        assert response.status_code == http.HTTPStatus.OK
        dialog_tag = content[content.index("<dialog") : content.index(">", content.index("<dialog"))]
        assert "open" in dialog_tag
        assert "Upload a valid image." in content
        room.refresh_from_db()
        assert not room.seal_image
