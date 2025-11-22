import http
import tempfile
from io import BytesIO

from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from apps.account.views import UserDetailView
from apps.core.tests.setup import BaseTestSetUp


class UserDetailViewTestCase(BaseTestSetUp):
    def _build_image_bytes(self, width=100, height=100):
        buffer = BytesIO()
        Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    def test_get_as_registered_user_own_profile(self):
        self.user.paypal_me_username = "paypal_username"
        self.user.save()

        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:detail", args=(self.user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()
        self.assertIn("Your account overview", stringed_content)
        self.assertIn(self.user.name, stringed_content)
        self.assertIn(self.user.email, stringed_content)
        self.assertIn(f"@{self.user.paypal_me_username}", stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_registered_user_other_profile_of_room(self):
        self.room.users.add(self.superuser)

        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:detail", args=(self.superuser.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()
        self.assertIn("Member profile", stringed_content)
        self.assertIn(self.superuser.name, stringed_content)
        self.assertIn(self.superuser.email, stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_registered_user_other_profile_who_is_not_in_room(self):
        """This can only happen if someone edits the URL"""
        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:detail", args=(self.superuser.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.FORBIDDEN)

        stringed_content = response.content.decode().replace("\n", "")
        self.assertIn("You are not allowed", stringed_content)
        self.assertIn("to see this page", stringed_content)

    def test_get_as_guest_own_profile(self):
        self.client.force_login(self.guest_user)
        response = self.client.get(reverse("account:detail", args=(self.guest_user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()
        self.assertIn("Guest Mode", stringed_content)
        self.assertIn("Hi", stringed_content)
        self.assertIn(self.guest_user.name, stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_guest_other_profile(self):
        self.user.paypal_me_username = "paypal_username"
        self.user.save()

        self.client.force_login(self.guest_user)
        response = self.client.get(reverse("account:detail", args=(self.user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()
        self.assertIn("Member profile", stringed_content)
        self.assertIn(self.user.name, stringed_content)
        self.assertIn(self.user.email, stringed_content)
        self.assertIn(f"@{self.user.paypal_me_username}", stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_get_as_superuser_own_profile(self):
        client = self.reauthenticate_user(self.superuser)
        response = client.get(reverse("account:detail", args=(self.superuser.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()
        self.assertIn("Your account overview", stringed_content)
        self.assertIn(self.superuser.name, stringed_content)
        self.assertIn(self.superuser.email, stringed_content)
        self.assertIn("id=superuser-admin-link", stringed_content, f"{stringed_content=}")

    def test_get_as_superuser_other_profile(self):
        self.assertFalse(
            self.superuser.rooms.all().exists(), "This test does not make sense, if the superuser belongs to a room"
        )

        client = self.reauthenticate_user(self.superuser)
        response = client.get(reverse("account:detail", args=(self.user.id,)))

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()
        self.assertIn("Member profile", stringed_content)
        self.assertIn(self.user.name, stringed_content)
        self.assertIn(self.user.email, stringed_content)

        self.assertNotIn('id="superuser-admin-link"', stringed_content)

    def test_profile_picture_shows_in_detail(self):
        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            self.user.profile_picture.save(
                "avatar.png",
                ContentFile(self._build_image_bytes()),
                save=True,
            )

            client = self.reauthenticate_user(self.user)
            response = client.get(reverse("account:detail", args=(self.user.id,)))

            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            content = response.content.decode()
            profile_picture_url = self.user.profile_picture_url
            has_src_with_quotes = f'src="{profile_picture_url}"' in content
            has_src_without_quotes = f"src={profile_picture_url}" in content
            self.assertTrue(
                has_src_with_quotes or has_src_without_quotes,
                msg=f"profile picture wasn't rendered with url {profile_picture_url}",
            )

    def test_profile_picture_fallbacks_to_default_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            self.user.profile_picture.save(
                "avatar.png",
                ContentFile(self._build_image_bytes()),
                save=True,
            )

            self.user.profile_picture.storage.delete(self.user.profile_picture.name)
            self.user.refresh_from_db()

            client = self.reauthenticate_user(self.user)
            response = client.get(reverse("account:detail", args=(self.user.id,)))

            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            fallback_url = self.user.profile_picture_fallback_url
            self.assertEqual(self.user.profile_picture_url, fallback_url)
