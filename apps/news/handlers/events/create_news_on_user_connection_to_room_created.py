from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.room.messages.events.user_connection_to_room_created import UserConnectionToRoomCreated


@message_registry.register_event(event=UserConnectionToRoomCreated)
def create_news_on_user_connection_to_room_created(context: UserConnectionToRoomCreated.Context):
    user_connection_to_room = context.instance

    added_user_name = (
        "themselves" if user_connection_to_room.created_by_is_connection_user else user_connection_to_room.user.name
    )
    message = (
        f'{user_connection_to_room.created_by.name} added {added_user_name} to "{user_connection_to_room.room.name}"'
    )

    News.objects.create(
        title=f"✨ {user_connection_to_room.room.display_initials}: User added",
        message=message,
        room_id=user_connection_to_room.room_id,
    )
