import http
import tempfile
from io import BytesIO

from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from PIL import Image

from apps.account.views import UserDetailView, UserUpdateView
from apps.core.tests.setup import BaseTestSetUp


class UserUpdateViewTestCase(BaseTestSetUp):
    def _build_image_bytes(self, width=100, height=100):
        buffer = BytesIO()
        Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()

    def test_get_regular(self):
        client = self.reauthenticate_user(self.user)
        response = client.get(reverse("account:update", kwargs={"pk": self.user.id}))
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], UserUpdateView.template_name)

        stringed_content = response.content.decode()

        self.assertIn("Keep your details up to date", stringed_content)
        self.assertIn("Need a new password?", stringed_content)

    def test_post_regular(self):
        new_name = "new_name"

        client = self.reauthenticate_user(self.user)
        response = client.post(
            reverse("account:update", kwargs={"pk": self.user.id}),
            data={"name": new_name, "email": self.user.email},
            follow=True,
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(response.template_name[0], UserDetailView.template_name)

        stringed_content = response.content.decode()

        self.assertIn("Your account overview", stringed_content)
        self.assertIn("Edit profile", stringed_content)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, new_name)

    def test_profile_picture_delete(self):
        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            self.user.profile_picture.save(
                "avatar.png",
                ContentFile(self._build_image_bytes()),
                save=True,
            )
            file_name = self.user.profile_picture.name
            self.assertTrue(self.user.profile_picture.storage.exists(file_name))

            client = self.reauthenticate_user(self.user)
            response = client.post(reverse("account:profile-picture-delete"), follow=True)
            self.assertEqual(response.status_code, http.HTTPStatus.OK)
            self.assertIn(UserUpdateView.template_name, response.template_name)

            self.user.refresh_from_db()
            self.assertFalse(self.user.profile_picture)
            self.assertFalse(self.user.profile_picture.storage.exists(file_name))
