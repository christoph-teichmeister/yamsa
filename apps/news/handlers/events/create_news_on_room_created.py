from django.urls import reverse

from apps.core.event_loop.registry import message_registry
from apps.news.models import News
from apps.room.messages.events.room_created import RoomCreated


@message_registry.register_event(event=RoomCreated)
def create_news_on_room_created(context: RoomCreated.Context):
    room = context.instance

    message = f'{room.created_by.name} created "{room.name}"'

    deeplink = reverse("room:detail", kwargs={"room_slug": room.slug})

    News.objects.create(
        title=f"🛠️ {room.capitalised_initials}: Created",
        message=message,
        room_id=room.id,
        deeplink=deeplink,
    )
