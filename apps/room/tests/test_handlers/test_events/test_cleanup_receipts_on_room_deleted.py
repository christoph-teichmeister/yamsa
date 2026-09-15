import pytest

from apps.room.handlers.events.cleanup_receipts_on_room_deleted import delete_receipt_files_on_room_deleted
from apps.room.messages.events.room_hard_deleted import RoomHardDeleted


class _StubStorage:
    def __init__(self):
        self.deleted_names: list[str] = []

    def delete(self, name):
        self.deleted_names.append(name)


@pytest.mark.django_db
def test_every_captured_receipt_file_is_deleted_from_its_storage():
    storage_a = _StubStorage()
    storage_b = _StubStorage()

    delete_receipt_files_on_room_deleted(
        RoomHardDeleted.Context(
            room_name="Ski trip",
            actor_name="Alice",
            member_user_ids=[],
            receipt_storage_refs=[(storage_a, "receipts/one.pdf"), (storage_b, "receipts/two.pdf")],
        )
    )

    assert storage_a.deleted_names == ["receipts/one.pdf"]
    assert storage_b.deleted_names == ["receipts/two.pdf"]


@pytest.mark.django_db
def test_no_receipts_is_a_no_op():
    delete_receipt_files_on_room_deleted(
        RoomHardDeleted.Context(
            room_name="Ski trip",
            actor_name="Alice",
            member_user_ids=[],
            receipt_storage_refs=[],
        )
    )
