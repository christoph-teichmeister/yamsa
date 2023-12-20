from apps.account.messages.commands.remove_user_from_room import RemoveUserFromRoom
from apps.account.messages.events.user_removed_from_room import UserRemovedFromRoom
from apps.core.event_loop.registry import message_registry


@message_registry.register_command(command=RemoveUserFromRoom)
def handle_remove_user_from_room(context: RemoveUserFromRoom.Context) -> UserRemovedFromRoom:
    context.user_to_be_removed.rooms.remove(context.room)

    return UserRemovedFromRoom(
        context_data={
            "room": context.room,
            "user_to_be_removed": context.user_to_be_removed,
            "user_requesting_removal": context.user_requesting_removal,
        }
    )
