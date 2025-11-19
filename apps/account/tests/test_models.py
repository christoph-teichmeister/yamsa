import tempfile
from io import BytesIO
from time import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import IntegrityError
from django.test import override_settings
from freezegun import freeze_time
from model_bakery import baker
from PIL import Image

from apps.account.models import UserFriendship
from apps.core.tests.setup import BaseTestSetUp
from apps.room.models import UserConnectionToRoom


def build_profile_picture_fallback_url():
    static_url = settings.STATIC_URL
    if not static_url.endswith("/"):
        static_url = f"{static_url}/"
    return f"{static_url}img/profile-default.svg"


class UserModelTestCase(BaseTestSetUp):
    def test_str_method(self):
        self.assertEqual(self.user.__str__(), self.user.name)

    def _build_image_bytes(self, width=64, height=64):
        buffer = BytesIO()
        Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    @freeze_time("2020-04-04 04:20:00")
    def test_clean_for_guests(self):
        timestamp = time()

        name_before = self.guest_user.name
        email_before = self.guest_user.email
        password_before = self.guest_user.password

        self.guest_user.clean()

        self.assertEqual(name_before, self.guest_user.name)
        self.assertNotEqual(email_before, self.guest_user.email)
        self.assertNotEqual(password_before, self.guest_user.password)

        self.assertEqual(self.guest_user.email, f"{self.guest_user.name}-{timestamp}@local.local")
        self.assertEqual(self.guest_user.password, f"{self.guest_user.name}-{timestamp}")

    def test_clean_for_regular_user(self):
        name_before = self.user.name
        email_before = self.user.email
        password_before = self.user.password

        self.user.clean()

        self.assertEqual(name_before, self.user.name)
        self.assertEqual(email_before, self.user.email)
        self.assertEqual(password_before, self.user.password)

    def test_room_qs_for_list_user(self):
        qs = self.user.room_qs_for_list

        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first()["name"], self.room.name)

    def test_room_qs_for_list_superuser(self):
        baker.make_recipe("apps.room.tests.room")

        qs = self.superuser.room_qs_for_list

        self.assertEqual(qs.count(), 2)

    def test_has_seen_room_true(self):
        connection = UserConnectionToRoom.objects.get(user=self.user)
        connection.user_has_seen_this_room = True
        connection.save()

        found_connection, has_seen_room = self.user.has_seen_room(self.room.id)

        self.assertTrue(has_seen_room)
        self.assertEqual(connection, found_connection)

    def test_has_seen_room_false(self):
        self.room.users.remove(self.user)

        connection, has_seen_room = self.user.has_seen_room(self.room.id)

        self.assertFalse(has_seen_room)
        self.assertIsNone(connection)

    def test_can_be_removed_from_room_true(self):
        self.assertTrue(self.user.can_be_removed_from_room(self.room.id))

    def test_can_be_removed_from_room_false(self):
        baker.make_recipe("apps.transaction.tests.parent_transaction", room=self.room, paid_by=self.user)

        self.assertFalse(self.user.can_be_removed_from_room(self.room.id))

    def test_generate_random_password_with_length(self):
        password_hash_before = self.user.password

        length = 10
        new_password = self.user.generate_random_password_with_length(length)
        self.assertEqual(len(new_password), length)

        self.user.refresh_from_db()

        self.assertNotEqual(password_hash_before, self.user.password)

    def test_profile_picture_url_defaults_to_placeholder(self):
        fallback_url = build_profile_picture_fallback_url()
        self.assertEqual(self.user.profile_picture_url, fallback_url)

    def test_profile_picture_url_returns_file_url_when_available(self):
        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            self.user.profile_picture.save(
                "avatar.png",
                ContentFile(self._build_image_bytes()),
                save=True,
            )

            self.assertEqual(self.user.profile_picture_url, self.user.profile_picture.url)

    def test_profile_picture_url_falls_back_when_file_missing(self):
        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            self.user.profile_picture.save(
                "avatar.png",
                ContentFile(self._build_image_bytes()),
                save=True,
            )

            self.user.profile_picture.storage.delete(self.user.profile_picture.name)
            self.user.refresh_from_db()

            fallback_url = build_profile_picture_fallback_url()
            self.assertEqual(self.user.profile_picture_url, fallback_url)


class UserFriendshipModelTestCase(BaseTestSetUp):
    def test_cannot_friend_self(self):
        friendship = UserFriendship(user=self.user, friend=self.user)

        with self.assertRaises(ValidationError):
            friendship.clean()

    def test_unique_constraint_applies(self):
        UserFriendship.objects.create(user=self.user, friend=self.guest_user)

        with self.assertRaises(IntegrityError):
            UserFriendship.objects.create(user=self.user, friend=self.guest_user)
