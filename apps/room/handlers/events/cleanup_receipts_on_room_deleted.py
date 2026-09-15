from apps.core.event_loop.registry import message_registry
from apps.room.messages.events.room_hard_deleted import RoomHardDeleted


@message_registry.register_event(event=RoomHardDeleted)
def delete_receipt_files_on_room_deleted(context: RoomHardDeleted.Context):
    for storage, name in context.receipt_storage_refs:
        storage.delete(name)
