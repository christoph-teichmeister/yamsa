import http

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import Client
from django.urls import reverse

from apps.account.tests.test_utils import build_image_bytes, contains_attribute

pytestmark = pytest.mark.django_db


def build_upload(file_name: str = "avatar.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(file_name, build_image_bytes(), content_type="image/png")


class TestUserProfilePictureUpdateView:
    def test_post_stores_the_picture_and_answers_with_the_photo_alone(
        self, tmp_path, settings, authenticated_client, user
    ):
        settings.MEDIA_ROOT = str(tmp_path)

        response = authenticated_client.post(
            reverse("account:profile-picture-update"),
            data={"profile_picture": build_upload()},
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        # Only the photo, so an upload never disturbs the sheet around it.
        assert contains_attribute(content, "id", "profile-photo")
        assert not contains_attribute(content, "id", "profile-sheet")

        user.refresh_from_db()
        assert user.profile_picture

    def test_post_leaves_the_rest_of_the_profile_untouched(self, tmp_path, settings, authenticated_client, user):
        settings.MEDIA_ROOT = str(tmp_path)
        original_name = user.name

        # A stale sheet would post its fields along; the picture view must ignore them.
        authenticated_client.post(
            reverse("account:profile-picture-update"),
            data={"profile_picture": build_upload(), "name": "posted-by-accident"},
        )

        user.refresh_from_db()
        assert user.name == original_name
        assert user.profile_picture

    def test_post_of_an_invalid_file_keeps_the_dialog_open_with_the_error(
        self, tmp_path, settings, authenticated_client, user
    ):
        settings.MEDIA_ROOT = str(tmp_path)
        corrupted = SimpleUploadedFile("avatar.bin", b"not-an-image", content_type="application/octet-stream")

        response = authenticated_client.post(
            reverse("account:profile-picture-update"),
            data={"profile_picture": corrupted},
        )

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        # Closing the dialog would hide the only explanation of why nothing happened.
        dialog_tag = content[content.index("<dialog") : content.index(">", content.index("<dialog"))]
        assert "open" in dialog_tag
        # ImageField rejects a non-image before the form's own PIL check gets to it.
        assert "Upload a valid image." in content

        user.refresh_from_db()
        assert not user.profile_picture

    def test_post_without_htmx_redirects_to_the_profile(self, tmp_path, settings, user):
        settings.MEDIA_ROOT = str(tmp_path)
        client = Client()
        client.force_login(user)

        response = client.post(
            reverse("account:profile-picture-update"),
            data={"profile_picture": build_upload()},
            follow=True,
        )

        assert response.status_code == http.HTTPStatus.OK
        assert response.redirect_chain[-1][0] == reverse("account:detail", kwargs={"pk": user.id})

        user.refresh_from_db()
        assert user.profile_picture
