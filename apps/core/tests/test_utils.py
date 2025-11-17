from uuid import UUID

from django.test import SimpleTestCase

from apps.core.utils import determine_upload_to


class DummyMeta:
    def __init__(self, app_label: str, model_name: str):
        self.app_label = app_label
        self.model_name = model_name


class DummyInstance:
    def __init__(self, app_label: str, model_name: str, upload_folder_name: str | None):
        self._meta = DummyMeta(app_label, model_name)
        self.UPLOAD_FOLDER_NAME = upload_folder_name


class DetermineUploadToTests(SimpleTestCase):
    def test_generates_uuid_prefixed_filename_with_folder(self):
        instance = DummyInstance("account", "user", "profile_picture")
        path = determine_upload_to(instance, "avatar.png")
        self.assertTrue(path.startswith("account/user/profile_picture/"))

        unique_segment = path.split("/")[-1]
        uuid_part, stored_name = unique_segment.rsplit("-", 1)
        UUID(uuid_part)  # Will raise if the uuid is malformed.
        self.assertEqual(stored_name, "avatar.png")

    def test_generates_different_values_for_same_filename(self):
        instance = DummyInstance("account", "user", "profile_picture")
        first_path = determine_upload_to(instance, "avatar.png")
        second_path = determine_upload_to(instance, "avatar.png")
        self.assertNotEqual(first_path, second_path)

    def test_appends_uuid_without_folder_when_not_configured(self):
        instance = DummyInstance("room", "booking", None)
        path = determine_upload_to(instance, "room.jpg")
        self.assertTrue(path.startswith("room/booking/"))
        uuid_part, stored_name = path.split("/")[-1].rsplit("-", 1)
        UUID(uuid_part)
        self.assertEqual(stored_name, "room.jpg")
