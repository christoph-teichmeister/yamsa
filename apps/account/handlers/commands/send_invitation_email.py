from django.utils import timezone

from apps.account.messages.commands.send_invitation_email import SendInvitationEmail
from apps.account.messages.events.invitation_email_sent import InvitationEmailSent
from apps.core.event_loop.registry import message_registry
from apps.mail.services.send_invitation_mail_service import InvitationEmailService


@message_registry.register_command(command=SendInvitationEmail)
def handle_remove_user_from_room(context: SendInvitationEmail.Context) -> InvitationEmailSent:
    service = InvitationEmailService(
        invited_by=context.inviter, recipient=context.invitee, recipient_email_list=[context.invitee_email]
    )
    service.process()

    context.invitee.invitation_email_sent = True
    context.invitee.invitation_email_sent_at = timezone.now()
    context.invitee.save()

    return InvitationEmailSent(
        context_data={
            "invitee": context.invitee,
            "invitee_email": context.invitee_email,
            "inviter": context.inviter,
        }
    )
