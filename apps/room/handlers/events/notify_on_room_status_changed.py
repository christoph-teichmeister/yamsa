from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from apps.account.utils.language import get_language_code_for_user
from apps.core.event_loop.registry import message_registry
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room
from apps.webpush.utils import Notification


@message_registry.register_event(event=RoomStatusChanged)
def send_notification_on_room_status_changed(context: RoomStatusChanged.Context):
    room = context.room

    # Notify users when a room is closed
    if room.status == Room.StatusChoices.CLOSED:
        for user in room.room_users.exclude(id=room.lastmodified_by.id):
            with translation.override(get_language_code_for_user(user)):
                head = _("Room closed")
                body = _('{editor} closed "{room}"').format(editor=room.lastmodified_by.name, room=room.name)

            Notification(
                payload=Notification.Payload(
                    head=head,
                    body=body,
                    click_url=reverse("room:detail", kwargs={"room_slug": room.slug}),
                ),
            ).send_to_user(user)

    # Notify users when a room is reopened
    if room.status == Room.StatusChoices.OPEN:
        for user in room.room_users.exclude(id=room.lastmodified_by.id):
            with translation.override(get_language_code_for_user(user)):
                head = _("Room re-opened")
                body = _('{editor} opened "{room}"').format(editor=room.lastmodified_by.name, room=room.name)

            Notification(
                payload=Notification.Payload(
                    head=head,
                    body=body,
                    click_url=reverse("room:detail", kwargs={"room_slug": room.slug}),
                ),
            ).send_to_user(user)
