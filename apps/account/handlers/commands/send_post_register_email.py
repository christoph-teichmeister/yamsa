from apps.account.messages.commands.send_post_register_email import SendPostRegisterEmail
from apps.account.messages.events.post_register_email_sent import PostRegisterEmailSent
from apps.core.event_loop.registry import message_registry
from apps.mail.services.post_register_mail_service import PostRegisterEmailService


@message_registry.register_command(command=SendPostRegisterEmail)
def handle_send_post_register_mail(context: SendPostRegisterEmail.Context) -> PostRegisterEmailSent:
    service = PostRegisterEmailService(recipient=context.user)
    service.process()

    return PostRegisterEmailSent(context_data={"user": context.user})
