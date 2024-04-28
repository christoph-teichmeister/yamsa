from apps.core.event_loop.registry import message_registry
from apps.room.messages.events.user_connection_to_room_created import UserConnectionToRoomCreated


@message_registry.register_event(event=UserConnectionToRoomCreated)
def send_notification_on_user_connection_to_room_created(context: UserConnectionToRoomCreated.Context):
    # room = context.room
    #
    # # Notify users when a room is closed
    # if room.status == Room.StatusChoices.CLOSED:
    #     notification = Notification(
    #         payload=Notification.Payload(
    #             head="Room closed",
    #             body=f'{room.lastmodified_by.name} closed "{room.name}"',
    #         ),
    #     )
    #     for user in room.room_users.exclude(id=room.lastmodified_by.id):
    #         notification.payload.click_url = reverse("room:detail", kwargs={"room_slug": room.slug})
    #         notification.send_to_user(user)
    #
    # # Notify users when a room is reopened
    # if room.status == Room.StatusChoices.OPEN:
    #     notification = Notification(
    #         payload=Notification.Payload(
    #             head="Room re-opened",
    #             body=f'{room.lastmodified_by.name} opened "{room.name}"',
    #         ),
    #     )
    #     for user in room.room_users.exclude(id=room.lastmodified_by.id):
    #         notification.payload.click_url = reverse("room:detail", kwargs={"room_slug": room.slug})
    #         notification.send_to_user(user)
    pass
