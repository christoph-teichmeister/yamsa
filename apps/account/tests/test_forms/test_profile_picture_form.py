import tempfile
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile, SimpleUploadedFile
from django.test import override_settings
from PIL import Image

from apps.account.forms import ProfilePictureForm
from apps.core.services.compress_picture_service import (
    MAX_PROFILE_PICTURE_DIMENSION,
    MAX_PROFILE_PICTURE_FILE_SIZE,
    CompressPictureService,
)


class TestProfilePictureForm:
    form_class = ProfilePictureForm

    @staticmethod
    def _build_image_file(width=200, height=200):
        buffer = BytesIO()
        Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
        buffer.seek(0)
        return SimpleUploadedFile("avatar.png", buffer.read(), content_type="image/png")

    def test_upload_saves_file(self, user):
        image_file = self._build_image_file()

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(instance=user, data={}, files={"profile_picture": image_file})
            assert form.is_valid()
            form.save()

            user.refresh_from_db()
            assert user.profile_picture
            stored_name = user.profile_picture.name
            assert user.profile_picture.storage.exists(stored_name)

    def test_upload_saves_file_with_long_filename(self, user):
        """Regression test for #YAMSA-45: uuid4()-prefixed long Android filenames overflowed the
        old ImageField max_length=100, raising a DataError on save()."""
        buffer = BytesIO()
        Image.new("RGB", (200, 200), color=(255, 255, 255)).save(buffer, format="PNG")
        buffer.seek(0)
        long_filename = "IMG_20260902_142233857_HDR_from_google_photos_backup_edited_final_v2.png"
        image_file = SimpleUploadedFile(long_filename, buffer.read(), content_type="image/png")

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(instance=user, data={}, files={"profile_picture": image_file})
            assert form.is_valid()
            form.save()

            user.refresh_from_db()
            assert user.profile_picture
            assert user.profile_picture.storage.exists(user.profile_picture.name)

    def test_upload_resizes_to_maximum_dimensions(self, user):
        image_file = self._build_image_file(
            width=MAX_PROFILE_PICTURE_DIMENSION * 2,
            height=MAX_PROFILE_PICTURE_DIMENSION * 2,
        )

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(instance=user, data={}, files={"profile_picture": image_file})
            assert form.is_valid()
            form.save()

            user.refresh_from_db()
            stored_name = user.profile_picture.name
            assert user.profile_picture.storage.exists(stored_name)
            with user.profile_picture.storage.open(stored_name) as stored_file, Image.open(stored_file) as saved_image:
                assert saved_image.width <= MAX_PROFILE_PICTURE_DIMENSION
                assert saved_image.height <= MAX_PROFILE_PICTURE_DIMENSION

            assert user.profile_picture.storage.size(stored_name) <= MAX_PROFILE_PICTURE_FILE_SIZE

    def test_rejects_invalid_uploads(self, user):
        corrupted_file = SimpleUploadedFile(
            "avatar.bin",
            b"not-an-image",
            content_type="application/octet-stream",
        )

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(instance=user, data={}, files={"profile_picture": corrupted_file})

            assert not form.is_valid()
            assert "profile_picture" in form.errors

    def test_surfaces_compressor_errors(self, user, monkeypatch):
        image_file = self._build_image_file()

        def fail(self) -> None:
            raise RuntimeError("failed")  # noqa: EM101

        monkeypatch.setattr(CompressPictureService, "process", fail)

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            form = self.form_class(instance=user, data={}, files={"profile_picture": image_file})

            assert not form.is_valid()
            assert form.errors.get("profile_picture") or form.non_field_errors()

    def test_rejects_uncompressed_oversized_images(self, user, monkeypatch):
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
            form = self.form_class(instance=user, data={}, files={"profile_picture": image_file})

            assert not form.is_valid()
            assert form.errors.get("profile_picture") or form.non_field_errors()

    def test_saving_without_a_file_keeps_the_stored_picture(self, user):
        """The profile save posts no file, so an empty form must never clear the avatar."""

        with tempfile.TemporaryDirectory() as tmp_media_root, override_settings(MEDIA_ROOT=tmp_media_root):
            setup_form = self.form_class(instance=user, data={}, files={"profile_picture": self._build_image_file()})
            assert setup_form.is_valid()
            setup_form.save()
            user.refresh_from_db()
            stored_name = user.profile_picture.name

            form = self.form_class(instance=user, data={}, files={})
            assert form.is_valid()
            form.save()

            user.refresh_from_db()
            assert user.profile_picture.name == stored_name
