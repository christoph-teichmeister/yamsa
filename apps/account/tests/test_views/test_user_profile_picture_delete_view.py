import http

import pytest
from django.core.files.base import ContentFile
from django.test.client import Client
from django.urls import reverse

from apps.account.tests.test_utils import build_image_bytes, contains_attribute

pytestmark = pytest.mark.django_db


@pytest.fixture
def user_with_profile_picture(tmp_path, settings, user):
    media_root = tmp_path / "media"
    media_root.mkdir()
    settings.MEDIA_ROOT = str(media_root)

    user.profile_picture.save("avatar.png", ContentFile(build_image_bytes()), save=True)
    assert user.profile_picture.storage.exists(user.profile_picture.name)
    return user


class TestUserProfilePictureDeleteView:
    def test_post_deletes_the_file_and_answers_with_the_unlocked_sheet(
        self, authenticated_client, user_with_profile_picture
    ):
        file_name = user_with_profile_picture.profile_picture.name

        response = authenticated_client.post(reverse("account:profile-picture-delete"))

        assert response.status_code == http.HTTPStatus.OK
        content = response.content.decode()
        # Removing the picture happens mid-edit, so the sheet comes back still editable.
        assert contains_attribute(content, "id", "profile-sheet")
        assert contains_attribute(content, "data-profile-mode", "editing")

        user_with_profile_picture.refresh_from_db()
        assert not user_with_profile_picture.profile_picture
        assert not user_with_profile_picture.profile_picture.storage.exists(file_name)

    def test_post_without_htmx_redirects_back_into_the_edit_state(self, user_with_profile_picture):
        client = Client()
        client.force_login(user_with_profile_picture)

        response = client.post(reverse("account:profile-picture-delete"), follow=True)

        assert response.status_code == http.HTTPStatus.OK
        assert response.redirect_chain[-1][0] == reverse("account:update", kwargs={"pk": user_with_profile_picture.id})
