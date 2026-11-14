from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext as _

from apps.account.models import User
from apps.account.utils.language import get_language_code_for_user
from apps.core.event_loop.registry import message_registry
from apps.mail.services.room_debts_force_settled_mail_service import RoomDebtsForceSettledEmailService
from apps.room.messages.events.room_debts_force_settled import RoomDebtsForceSettled
from apps.webpush.utils import Notification


def _recipients(context: RoomDebtsForceSettled.Context) -> list[User]:
    # The actor made the decision and needs no notice of it.
    return list(User.objects.filter(id__in=context.affected_user_ids).exclude(id=context.actor.id))


@message_registry.register_event(event=RoomDebtsForceSettled, atomic=False)
def send_notification_on_room_debts_force_settled(context: RoomDebtsForceSettled.Context) -> None:
    for user in _recipients(context):
        with translation.override(get_language_code_for_user(user)):
            head = _("Debts marked as settled")
            body = _('{editor} closed "{room}" and marked all open debts as settled').format(
                editor=context.actor.name, room=context.room.name
            )

        Notification(
            payload=Notification.Payload(
                head=head,
                body=body,
                click_url=reverse("debt:list", kwargs={"room_slug": context.room.slug}),
            ),
        ).send_to_user(user)


@message_registry.register_event(event=RoomDebtsForceSettled, atomic=False)
def send_email_on_room_debts_force_settled(context: RoomDebtsForceSettled.Context) -> None:
    for user in _recipients(context):
        # Guests have no real address.
        if user.is_guest:
            continue

        RoomDebtsForceSettledEmailService(recipient=user, room=context.room, actor_name=context.actor.name).process()
