import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.account.forms import EditUserForm
from apps.account.forms.edit_user_form import (
    MAX_PROFILE_PICTURE_DIMENSION,
    MAX_PROFILE_PICTURE_FILE_SIZE,
    PROFILE_PICTURE_DIMENSION_ERROR,
    PROFILE_PICTURE_SIZE_ERROR,
)
from apps.core.tests.setup import BaseTestSetUp
from apps.webpush.models import WebpushInformation


class EditUserFormTestCase(BaseTestSetUp):
    form = EditUserForm

    def _build_image_file(self, width=200, height=200):
        buffer = BytesIO()
        Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile("avatar.png", buffer.read(), content_type="image/png")

    def _base_form_data(self, **overrides):
        data = {
            "name": self.user.name,
            "email": self.user.email,
            "paypal_me_username": self.user.paypal_me_username or "",
            "wants_to_receive_webpush_notifications": self.user.wants_to_receive_webpush_notifications,
            "wants_to_receive_payment_reminders": self.user.wants_to_receive_payment_reminders,
            "wants_to_receive_room_reminders": self.user.wants_to_receive_room_reminders,
        }
        data.update(overrides)
        return data

    def test_regular(self):
        new_data = {
            "name": "new_name",
            "email": "new_email@local.local",
            "paypal_me_username": "new_paypal_me_username",
            "wants_to_receive_webpush_notifications": True,
            "wants_to_receive_payment_reminders": False,
        }

        form = self.form(instance=self.user, data=new_data)
        self.assertTrue(form.is_valid())

        form.save()
        self.user.refresh_from_db()

        for key in new_data:
            self.assertEqual(getattr(self.user, key), new_data[key])

    def test_required_fields(self):
        form = self.form(instance=self.user, data={})
        self.assertFalse(form.is_valid())

        required_message = "This field is required."

        self.assertEqual(form.errors["name"][0], required_message)
        self.assertEqual(form.errors["email"][0], required_message)

    def test_email_format(self):
        new_data = {"email": "wrong_format"}

        form = self.form(instance=self.user, data=new_data)
        self.assertFalse(form.is_valid())

        self.assertEqual(form.errors["email"][0], "Enter a valid email address.")

    def test_setting_wants_to_receive_webpush_notifications_to_false_deleted_any_webpush_infos(self):
        self.user.wants_to_receive_webpush_notifications = True
        self.user.save()
        WebpushInformation.objects.create(
            user=self.user,
            browser="a_browser",
            endpoint="http://an-endpoint.local",
            auth="auth_string",
            p256dh="p256dh_string",
        )

        self.assertTrue(WebpushInformation.objects.filter(user=self.user).exists())

        new_data = {
            "name": self.user.name,
            "email": self.user.email,
            "wants_to_receive_webpush_notifications": False,
            "wants_to_receive_payment_reminders": True,
        }

        form = self.form(instance=self.user, data=new_data)
        self.assertTrue(form.is_valid())

        form.save()

        self.assertFalse(self.user.wants_to_receive_webpush_notifications)
        self.assertFalse(WebpushInformation.objects.filter(user=self.user).exists())

    def test_profile_picture_upload_saves_file(self):
        form_data = self._base_form_data()
        image_file = self._build_image_file()

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form(instance=self.user, data=form_data, files={"profile_picture": image_file})
            self.assertTrue(form.is_valid())
            form.save()

            self.user.refresh_from_db()
            self.assertTrue(self.user.profile_picture)
            stored_name = self.user.profile_picture.name
            self.assertTrue(self.user.profile_picture.storage.exists(stored_name))

    def test_profile_picture_size_validation(self):
        form_data = self._base_form_data()
        image_file = self._build_image_file()
        image_file.size = MAX_PROFILE_PICTURE_FILE_SIZE + 1

        form = self.form(instance=self.user, data=form_data, files={"profile_picture": image_file})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["profile_picture"][0], PROFILE_PICTURE_SIZE_ERROR)

    def test_profile_picture_dimension_validation(self):
        form_data = self._base_form_data()
        image_file = self._build_image_file(
            width=MAX_PROFILE_PICTURE_DIMENSION + 300, height=MAX_PROFILE_PICTURE_DIMENSION + 300
        )

        form = self.form(instance=self.user, data=form_data, files={"profile_picture": image_file})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["profile_picture"][0], PROFILE_PICTURE_DIMENSION_ERROR)
