from uuid import UUID

from apps.core.tests.test_helpers.dummy_instance import DummyInstance
from apps.core.utils import determine_upload_to


def test_generates_uuid_prefixed_filename_when_folder_is_configured():
    instance = DummyInstance("account", "user", "profile_picture")
    path = determine_upload_to(instance, "avatar.png")
    assert path.startswith("account/user/profile_picture/")

    unique_segment = path.split("/")[-1]
    uuid_part, stored_name = unique_segment.rsplit("-", 1)
    UUID(uuid_part)
    assert stored_name == "avatar.png"


def test_generates_distinct_values_for_same_filename():
    instance = DummyInstance("account", "user", "profile_picture")
    first_path = determine_upload_to(instance, "avatar.png")
    second_path = determine_upload_to(instance, "avatar.png")
    assert first_path != second_path


def test_appends_uuid_without_folder_when_not_configured():
    instance = DummyInstance("room", "booking", None)
    path = determine_upload_to(instance, "room.jpg")
    assert path.startswith("room/booking/")
    uuid_part, stored_name = path.split("/")[-1].rsplit("-", 1)
    UUID(uuid_part)
    assert stored_name == "room.jpg"
