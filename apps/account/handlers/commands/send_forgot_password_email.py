from apps.account.messages.commands.send_forgot_password_email import SendForgotPasswordEmail
from apps.account.messages.events.forgot_password_email_sent import ForgotPasswordEmailSent
from apps.core.event_loop.registry import message_registry
from apps.mail.services.forgot_password_mail_service import ForgotPasswordEmailService


@message_registry.register_command(command=SendForgotPasswordEmail)
def handle_send_forgot_password_email(context: SendForgotPasswordEmail.Context) -> ForgotPasswordEmailSent:
    service = ForgotPasswordEmailService(recipient=context.user)
    service.process()

    return ForgotPasswordEmailSent(context_data={"user": context.user})
