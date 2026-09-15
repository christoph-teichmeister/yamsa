from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from apps.account.models import User
from apps.account.utils.language import get_language_code_for_user
from apps.core.event_loop.registry import message_registry
from apps.room.messages.events.room_hard_deleted import RoomHardDeleted
from apps.webpush.utils import Notification


@message_registry.register_event(event=RoomHardDeleted)
def send_notification_on_room_deleted(context: RoomHardDeleted.Context):
    for user in User.objects.filter(id__in=context.member_user_ids):
        with translation.override(get_language_code_for_user(user)):
            head = _("Room deleted")
            body = _('{editor} deleted "{room}"').format(editor=context.actor_name, room=context.room_name)

        Notification(
            payload=Notification.Payload(
                head=head,
                body=body,
                click_url=reverse("core:welcome"),
            ),
        ).send_to_user(user)
