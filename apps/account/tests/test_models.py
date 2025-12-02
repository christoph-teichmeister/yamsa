from io import BytesIO
from time import time

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.test import override_settings
from freezegun import freeze_time
from PIL import Image

from apps.account.models import UserFriendship
from apps.room.models import UserConnectionToRoom
from apps.room.tests.factories import RoomFactory
from apps.transaction.tests.factories import ParentTransactionFactory


def _build_image_bytes(width=64, height=64) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def test_str_method(user):
    assert str(user) == user.name


@freeze_time("2020-04-04 04:20:00")
def test_clean_for_guests(guest_user):
    timestamp = time()

    name_before = guest_user.name
    email_before = guest_user.email
    password_before = guest_user.password

    guest_user.clean()

    assert name_before == guest_user.name
    assert email_before != guest_user.email
    assert password_before != guest_user.password
    assert guest_user.email == f"{guest_user.name}-{timestamp}@local.local"
    assert guest_user.password == f"{guest_user.name}-{timestamp}"


def test_clean_for_regular_user(user):
    name_before = user.name
    email_before = user.email
    password_before = user.password

    user.clean()

    assert name_before == user.name
    assert email_before == user.email
    assert password_before == user.password


def test_room_qs_for_list_user(user, room):
    qs = user.room_qs_for_list

    assert qs.count() == 1
    assert qs.first()["name"] == room.name


def test_room_qs_for_list_superuser(superuser, room):
    _ = room  # ensure fixture creates first room for superuser
    RoomFactory()

    qs = superuser.room_qs_for_list

    assert qs.count() == 2


def test_has_seen_room_true(user, room):
    connection = UserConnectionToRoom.objects.get(user=user, room=room)
    connection.user_has_seen_this_room = True
    connection.save()

    found_connection, has_seen_room = user.has_seen_room(room.id)

    assert has_seen_room is True
    assert found_connection == connection


def test_has_seen_room_false(user, room):
    room.users.remove(user)

    connection, has_seen_room = user.has_seen_room(room.id)

    assert has_seen_room is False
    assert connection is None


def test_can_be_removed_from_room_true(user, room):
    assert user.can_be_removed_from_room(room.id) is True


def test_can_be_removed_from_room_false(user, room):
    ParentTransactionFactory(room=room, paid_by=user)

    assert user.can_be_removed_from_room(room.id) is False


def test_generate_random_password_with_length(user):
    password_hash_before = user.password

    length = 10
    new_password = user.generate_random_password_with_length(length)
    assert len(new_password) == length

    user.refresh_from_db()
    assert user.password != password_hash_before


def test_profile_picture_url_defaults_to_placeholder(user):
    fallback_url = user.profile_picture_fallback_url
    assert user.profile_picture_url == fallback_url


def test_profile_picture_url_returns_file_url_when_available(user, tmp_path):
    tmp_media_root = tmp_path / "media"
    tmp_media_root.mkdir()

    with override_settings(MEDIA_ROOT=str(tmp_media_root)):
        user.profile_picture.save(
            "avatar.png",
            ContentFile(_build_image_bytes()),
            save=True,
        )

        assert user.profile_picture_url == user.profile_picture.url


def test_profile_picture_url_falls_back_when_file_missing(user, tmp_path):
    tmp_media_root = tmp_path / "media"
    tmp_media_root.mkdir()

    with override_settings(MEDIA_ROOT=str(tmp_media_root)):
        user.profile_picture.save(
            "avatar.png",
            ContentFile(_build_image_bytes()),
            save=True,
        )

        user.profile_picture.storage.delete(user.profile_picture.name)
        user.refresh_from_db()

        fallback_url = user.profile_picture_fallback_url
        assert user.profile_picture_url == fallback_url


def test_cannot_friend_self(user):
    friendship = UserFriendship(user=user, friend=user)

    with pytest.raises(ValidationError):
        friendship.clean()


def test_unique_constraint_applies(user, guest_user):
    UserFriendship.objects.create(user=user, friend=guest_user)

    with pytest.raises(IntegrityError):
        UserFriendship.objects.create(user=user, friend=guest_user)
