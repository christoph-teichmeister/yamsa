import http
from io import BytesIO

import pytest
from django.core.files.base import ContentFile
from django.urls import reverse
from PIL import Image

from apps.account.views import UserDetailView

pytestmark = pytest.mark.django_db


def build_image_bytes(width=100, height=100):
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def test_get_as_registered_user_own_profile(authenticated_client, user):
    user.paypal_me_username = "paypal_username"
    user.save()

    response = authenticated_client.get(reverse("account:detail", args=(user.id,)))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name

    content = response.content.decode()
    assert "Your account overview" in content
    assert user.name in content
    assert user.email in content
    assert f"@{user.paypal_me_username}" in content
    assert 'id="superuser-admin-link"' not in content


def test_get_as_registered_user_other_profile_of_room(authenticated_client, room, superuser):
    room.users.add(superuser)

    response = authenticated_client.get(reverse("account:detail", args=(superuser.id,)))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name

    content = response.content.decode()
    assert "Member profile" in content
    assert superuser.name in content
    assert superuser.email in content
    assert 'id="superuser-admin-link"' not in content


def test_get_as_registered_user_other_profile_who_is_not_in_room(authenticated_client, superuser):
    response = authenticated_client.get(reverse("account:detail", args=(superuser.id,)))

    assert response.status_code == http.HTTPStatus.FORBIDDEN

    content = response.content.decode().replace("\n", "")
    assert "You are not allowed" in content
    assert "to see this page" in content


def test_get_as_guest_own_profile(client, guest_user):
    client.force_login(guest_user)
    response = client.get(reverse("account:detail", args=(guest_user.id,)))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name

    content = response.content.decode()
    assert "Guest Mode" in content
    assert "Hi" in content
    assert guest_user.name in content
    assert 'id="superuser-admin-link"' not in content


def test_get_as_guest_other_profile(client, guest_user, user, room):
    client.force_login(guest_user)
    user.paypal_me_username = "paypal_username"
    user.save()

    assert room.users.filter(id=guest_user.id).exists()

    response = client.get(reverse("account:detail", args=(user.id,)))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name

    content = response.content.decode()
    assert "Member profile" in content
    assert user.name in content
    assert user.email in content
    assert f"@{user.paypal_me_username}" in content
    assert 'id="superuser-admin-link"' not in content


def test_get_as_superuser_own_profile(client, superuser):
    client.defaults["HTTP_HX_REQUEST"] = "true"
    client.force_login(superuser)

    response = client.get(reverse("account:detail", args=(superuser.id,)))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name

    content = response.content.decode()
    assert "Your account overview" in content
    assert superuser.name in content
    assert superuser.email in content
    assert 'id="superuser-admin-link"' in content


def test_get_as_superuser_other_profile(client, superuser, user):
    client.defaults["HTTP_HX_REQUEST"] = "true"
    client.force_login(superuser)

    assert not superuser.rooms.all().exists()

    response = client.get(reverse("account:detail", args=(user.id,)))

    assert response.status_code == http.HTTPStatus.OK
    assert response.template_name[0] == UserDetailView.template_name

    content = response.content.decode()
    assert "Member profile" in content
    assert user.name in content
    assert user.email in content
    assert 'id="superuser-admin-link"' not in content


def test_profile_picture_shows_in_detail(tmp_path, authenticated_client, settings, user):
    media_root = tmp_path / "media"
    media_root.mkdir()
    settings.MEDIA_ROOT = str(media_root)

    user.profile_picture.save("avatar.png", ContentFile(build_image_bytes()), save=True)

    response = authenticated_client.get(reverse("account:detail", args=(user.id,)))

    assert response.status_code == http.HTTPStatus.OK
    content = response.content.decode()
    profile_picture_url = user.profile_picture_url
    has_src_with_quotes = f'src="{profile_picture_url}"' in content
    has_src_without_quotes = f"src={profile_picture_url}" in content
    assert has_src_with_quotes or has_src_without_quotes


def test_profile_picture_fallbacks_to_default_when_missing(tmp_path, authenticated_client, settings, user):
    media_root = tmp_path / "media"
    media_root.mkdir()
    settings.MEDIA_ROOT = str(media_root)

    user.profile_picture.save("avatar.png", ContentFile(build_image_bytes()), save=True)
    file_name = user.profile_picture.name
    user.profile_picture.storage.delete(file_name)
    user.refresh_from_db()

    response = authenticated_client.get(reverse("account:detail", args=(user.id,)))

    assert response.status_code == http.HTTPStatus.OK
    fallback_url = user.profile_picture_fallback_url
    assert user.profile_picture_url == fallback_url
