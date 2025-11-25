from django.urls import reverse
from django.utils.translation import gettext as _

from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.room.messages.events.user_connection_to_room_created import UserConnectionToRoomCreated


@message_registry.register_event(event=UserConnectionToRoomCreated)
def create_news_on_user_connection_to_room_created(context: UserConnectionToRoomCreated.Context):
    user_connection_to_room = context.instance

    added_user_name = (
        _("themselves") if user_connection_to_room.created_by_is_connection_user else user_connection_to_room.user.name
    )
    created_by_name = user_connection_to_room.created_by.name if user_connection_to_room.created_by else _("System")
    message = _('{created_by} added {added_user} to "{room_name}"').format(
        created_by=created_by_name,
        added_user=added_user_name,
        room_name=user_connection_to_room.room.name,
    )

    deeplink = reverse("account:list", kwargs={"room_slug": user_connection_to_room.room.slug})

    News.objects.create(
        title=_("{icon} {initials}: User added").format(
            icon="✨",
            initials=user_connection_to_room.room.capitalised_initials,
        ),
        message=message,
        room_id=user_connection_to_room.room_id,
        deeplink=deeplink,
        type=News.TypeChoices.USER_ADDED,
    )
