from django.urls import reverse

from apps.core.event_loop.registry import message_registry
from apps.mail.services.user_added_to_room_mail_service import UserAddedToRoomEmailService
from apps.room.messages.events.user_connection_to_room_created import UserConnectionToRoomCreated
from apps.webpush.utils import Notification


@message_registry.register_event(event=UserConnectionToRoomCreated)
def send_notification_on_user_connection_to_room_created(context: UserConnectionToRoomCreated.Context):
    user_connection_to_room = context.instance

    # Do not notify the user who has just created the room (and hence a user_connection_to_room for himself)
    if user_connection_to_room.created_by_is_connection_user or user_connection_to_room.user.is_guest:
        return

    # Notify users that they have been added to a room
    notification = Notification(
        payload=Notification.Payload(
            head="New Room",
            body=f"You have been added to {user_connection_to_room.room.name}!",
            click_url=reverse("room:detail", kwargs={"room_slug": user_connection_to_room.room.slug}),
        ),
    )
    notification.send_to_user(user_connection_to_room.user)


@message_registry.register_event(event=UserConnectionToRoomCreated)
def send_email_on_user_connection_to_room_created(context: UserConnectionToRoomCreated.Context):
    user_connection_to_room = context.instance

    # Do not email the user who has just created the room (and hence a user_connection_to_room for himself),
    # or if they are a guest. As guest, they do not have real emails
    if user_connection_to_room.created_by_is_connection_user or user_connection_to_room.user.is_guest:
        return

    service = UserAddedToRoomEmailService(recipient=user_connection_to_room.user, new_room=user_connection_to_room.room)
    service.process()

    # TODO CT: Do this
    # return PostRegisterEmailSent(context_data={"user": context.user})
