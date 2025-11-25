from django.urls import reverse
from django.utils.translation import gettext as _

from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.room.messages.events.room_created import RoomCreated


@message_registry.register_event(event=RoomCreated)
def create_news_on_room_created(context: RoomCreated.Context):
    room = context.instance

    message = _('{creator} created "{room_name}"').format(
        creator=room.created_by.name,
        room_name=room.name,
    )

    deeplink = reverse("room:detail", kwargs={"room_slug": room.slug})

    News.objects.create(
        title=_("{icon} {initials}: Created").format(
            icon="🛠️",
            initials=room.capitalised_initials,
        ),
        message=message,
        room_id=room.id,
        deeplink=deeplink,
        type=News.TypeChoices.ROOM_CREATED,
    )
