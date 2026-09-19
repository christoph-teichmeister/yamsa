import http

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.account.tests.test_utils import build_image_bytes
from apps.room.room_seal import SEAL_ICONS

pytestmark = pytest.mark.django_db


def build_upload(file_name: str = "seal.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(file_name, build_image_bytes(), content_type="image/png")


class TestRoomSealResetView:
    def test_post_clears_both_the_icon_and_the_image(self, tmp_path, settings, authenticated_client, room):
        settings.MEDIA_ROOT = str(tmp_path)
        room.seal_icon = SEAL_ICONS[0]
        room.seal_image = build_upload()
        room.save(update_fields=["seal_icon", "seal_image"])

        response = authenticated_client.post(reverse("room:seal-reset", kwargs={"room_slug": room.slug}))

        assert response.status_code == http.HTTPStatus.OK
        room.refresh_from_db()
        assert room.seal_icon == ""
        assert not room.seal_image
