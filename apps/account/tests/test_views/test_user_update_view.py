import http
from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from PIL import Image

from apps.account.views import UserDetailView, UserUpdateView

pytestmark = pytest.mark.django_db


def build_image_bytes(width=100, height=100):
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def test_get_regular(authenticated_client, user):
    response = authenticated_client.get(reverse("account:update", kwargs={"pk": user.id}))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserUpdateView.template_name

    content = response.content.decode()
    assert "Keep your details up to date" in content
    assert "Need a new password?" in content


def test_post_regular(authenticated_client, user):
    new_name = "new_name"
    response = authenticated_client.post(
        reverse("account:update", kwargs={"pk": user.id}),
        data={"name": new_name, "email": user.email},
        follow=True,
    )

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name

    content = response.content.decode()
    assert "Your account overview" in content
    assert "Edit profile" in content

    user.refresh_from_db()
    assert user.name == new_name


def test_profile_picture_delete(tmp_path, authenticated_client, settings, user):
    media_root = tmp_path / "media"
    media_root.mkdir()
    settings.MEDIA_ROOT = str(media_root)

    user.profile_picture.save("avatar.png", ContentFile(build_image_bytes()), save=True)
    file_name = user.profile_picture.name
    assert user.profile_picture.storage.exists(file_name)

    response = authenticated_client.post(reverse("account:profile-picture-delete"), follow=True)

    assert response.status_code == http.HTTPStatus.OK
    assert UserUpdateView.template_name in response.template_name

    user.refresh_from_db()
    assert not user.profile_picture
    assert not user.profile_picture.storage.exists(file_name)
