from dataclasses import dataclass

from django_pony_express.services.base import BaseEmailService

from apps.account.models import User


@dataclass
class EmailBaseTextContext:
    SUBJECT_PREFIX: str = "yamsa | "

    header: str = "yamsa"
    # footer: str = "Your yamsa team"
    footer: str = ""
    sub_footer: str = "yamsa | Yet another money split app"


@dataclass
class EmailUserTextContext:
    greeting_prefix: str = "Hey"
    greeting_suffix: str = "👋"

    user: User = None
    text_list: list[str] = NotImplemented


@dataclass
class EmailExtraContext:
    show_unsubscribe = False
    unsubscribe_link: str = ""

    show_cta: bool = False
    cta_btn_link: str = ""
    cta_btn_text: str = ""


class BaseYamsaEmailService(BaseEmailService):
    FROM_EMAIL = "yamsa.hello@gmail.com"
    REPLY_TO_ADDRESS = "yamsa.hello+reply@gmail.com"

    recipient: User = None

    email_base_text_context: EmailBaseTextContext = EmailBaseTextContext()
    email_user_text_context: EmailUserTextContext = EmailUserTextContext()
    email_extra_context: EmailExtraContext = EmailExtraContext()

    template_name = "mail/email_text_base.html"

    def __init__(self, recipient: User, recipient_email_list: list | (tuple | str) | None = None, *args, **kwargs) -> None:
        self.recipient = recipient

        super().__init__(recipient_email_list or [recipient.email], *args, **kwargs)

    def get_subject(self) -> str:
        return self.email_base_text_context.SUBJECT_PREFIX + self.subject

    def get_context_data(self) -> dict:
        return {
            "context": {
                "subject": self.get_subject(),
                "greeting": self.get_greeting(),
                **self.get_email_base_text_context().__dict__,
                **self.get_email_user_text_context().__dict__,
                **self.get_email_extra_context().__dict__,
            }
        }

    def get_greeting(self):
        context = self.email_user_text_context

        if self.recipient is not None:
            return f"{context.greeting_prefix} {self.recipient.name} {context.greeting_suffix}"
        return f"{context.greeting_prefix} {context.greeting_suffix}"

    def get_email_base_text_context(self):
        return self.email_base_text_context

    def get_email_user_text_context(self):
        return self.email_user_text_context

    def get_email_extra_context(self):
        return self.email_extra_context
