from apps.core.event_loop.registry import message_registry
from apps.room.messages.commands.delete_room import DeleteRoom
from apps.room.messages.events.room_hard_deleted import RoomHardDeleted
from apps.transaction.models import Receipt


@message_registry.register_command(command=DeleteRoom)
def handle_delete_room(context: DeleteRoom.Context) -> RoomHardDeleted:
    room = context.room
    actor = context.user_requesting_deletion

    # Captured before the delete: the cascade takes the room's own rows (transactions, debts,
    # receipts, news, memberships) with it, so anything the follow-up event still needs has to be
    # read out first.
    room_name = room.name
    member_user_ids = list(room.room_users.exclude(id=actor.id).values_list("id", flat=True))
    receipt_storage_refs = [
        (receipt.file.storage, receipt.file.name)
        for receipt in Receipt.objects.filter(parent_transaction__room=room).exclude(file="")
    ]

    room.delete()

    return RoomHardDeleted(
        context_data={
            "room_name": room_name,
            "actor_name": actor.name,
            "member_user_ids": member_user_ids,
            "receipt_storage_refs": receipt_storage_refs,
        }
    )
