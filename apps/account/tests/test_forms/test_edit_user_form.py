import tempfile
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.account.forms import EditUserForm
from apps.core.services.compress_picture_service import (
    MAX_PROFILE_PICTURE_DIMENSION,
    MAX_PROFILE_PICTURE_FILE_SIZE,
    CompressPictureService,
)
from apps.webpush.models import WebpushInformation


class TestEditUserForm:
    form_class = EditUserForm

    @staticmethod
    def _build_image_file(width=200, height=200):
        buffer = BytesIO()
        Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile("avatar.png", buffer.read(), content_type="image/png")

    @staticmethod
    def _base_form_data(user, **overrides):
        data = {
            "name": user.name,
            "email": user.email,
            "paypal_me_username": user.paypal_me_username or "",
            "wants_to_receive_webpush_notifications": user.wants_to_receive_webpush_notifications,
            "wants_to_receive_payment_reminders": user.wants_to_receive_payment_reminders,
            "wants_to_receive_room_reminders": user.wants_to_receive_room_reminders,
        }
        data.update(overrides)
        return data

    def test_regular(self, user):
        new_data = {
            "name": "new_name",
            "email": "new_email@local.local",
            "paypal_me_username": "new_paypal_me_username",
            "wants_to_receive_webpush_notifications": True,
            "wants_to_receive_payment_reminders": False,
        }

        form = self.form_class(instance=user, data=new_data)
        assert form.is_valid()

        form.save()
        user.refresh_from_db()

        for key, value in new_data.items():
            assert getattr(user, key) == value

    def test_required_fields(self, user):
        form = self.form_class(instance=user, data={})
        assert not form.is_valid()

        required_message = "This field is required."

        assert form.errors["name"][0] == required_message
        assert form.errors["email"][0] == required_message

    def test_email_format(self, user):
        form = self.form_class(instance=user, data={"email": "wrong_format"})
        assert not form.is_valid()

        assert form.errors["email"][0] == "Enter a valid email address."

    def test_setting_wants_to_receive_webpush_notifications_to_false_deleted_any_webpush_infos(self, user):
        user.wants_to_receive_webpush_notifications = True
        user.save()
        WebpushInformation.objects.create(
            user=user,
            browser="a_browser",
            endpoint="http://an-endpoint.local",
            auth="auth_string",
            p256dh="p256dh_string",
        )

        assert WebpushInformation.objects.filter(user=user).exists()

        form = self.form_class(
            instance=user,
            data={
                "name": user.name,
                "email": user.email,
                "wants_to_receive_webpush_notifications": False,
                "wants_to_receive_payment_reminders": True,
            },
        )
        assert form.is_valid()

        form.save()

        assert not user.wants_to_receive_webpush_notifications
        assert not WebpushInformation.objects.filter(user=user).exists()

    def test_profile_picture_upload_saves_file(self, user):
        form_data = self._base_form_data(user)
        image_file = self._build_image_file()

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(instance=user, data=form_data, files={"profile_picture": image_file})
            assert form.is_valid()
            form.save()

            user.refresh_from_db()
            assert user.profile_picture
            stored_name = user.profile_picture.name
            assert user.profile_picture.storage.exists(stored_name)

    def test_profile_picture_resizes_to_maximum_dimensions(self, user):
        form_data = self._base_form_data(user)
        image_file = self._build_image_file(
            width=MAX_PROFILE_PICTURE_DIMENSION * 2,
            height=MAX_PROFILE_PICTURE_DIMENSION * 2,
        )

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(instance=user, data=form_data, files={"profile_picture": image_file})
            assert form.is_valid()
            form.save()

            user.refresh_from_db()
            stored_name = user.profile_picture.name
            assert user.profile_picture.storage.exists(stored_name)
            with user.profile_picture.storage.open(stored_name) as stored_file, Image.open(stored_file) as saved_image:
                assert saved_image.width <= MAX_PROFILE_PICTURE_DIMENSION
                assert saved_image.height <= MAX_PROFILE_PICTURE_DIMENSION

            assert user.profile_picture.storage.size(stored_name) <= MAX_PROFILE_PICTURE_FILE_SIZE

    def test_profile_picture_rejects_invalid_uploads(self, user):
        form_data = self._base_form_data(user)
        corrupted_file = SimpleUploadedFile(
            "avatar.bin",
            b"not-an-image",
            content_type="application/octet-stream",
        )

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(
                instance=user,
                data=form_data,
                files={"profile_picture": corrupted_file},
            )

            assert not form.is_valid()
            assert "profile_picture" in form.errors

    def test_profile_picture_surface_compressor_errors(self, user, monkeypatch):
        form_data = self._base_form_data(user)
        image_file = self._build_image_file()

        def fail(self) -> None:
            raise RuntimeError("failed")  # noqa: EM101

        monkeypatch.setattr(CompressPictureService, "process", fail)

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(
                instance=user,
                data=form_data,
                files={"profile_picture": image_file},
            )

            assert not form.is_valid()
            assert form.errors.get("profile_picture") or form.non_field_errors()

    def test_profile_picture_rejects_uncompressed_oversized_images(self, user, monkeypatch):
        form_data = self._base_form_data(user)
        image_file = self._build_image_file()

        def return_large_file(self):
            oversized_buffer = BytesIO(b"\x00" * (MAX_PROFILE_PICTURE_FILE_SIZE + 1024))
            oversized_buffer.seek(0)
            return InMemoryUploadedFile(
                oversized_buffer,
                "profile_picture",
                "oversized.jpg",
                "image/jpeg",
                oversized_buffer.getbuffer().nbytes,
                None,
            )

        monkeypatch.setattr(CompressPictureService, "process", return_large_file)

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(
                instance=user,
                data=form_data,
                files={"profile_picture": image_file},
            )

            assert not form.is_valid()
            assert form.errors.get("profile_picture") or form.non_field_errors()
