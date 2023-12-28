from dataclasses import dataclass

from django_pony_express.services.base import BaseEmailService


@dataclass
class YamsaEmailSettings:
    SUBJECT_PREFIX: str = "yamsa | "

    header: str = "yamsa"
    footer: str = "Your yamsa team"
    sub_footer: str = "yamsa | Yet another money split app"

    greeting_prefix: str = "Hey "
    greeting_suffix: str = "👋"


@dataclass
class YamsaEmailContext:
    show_unsubscribe = False
    unsubscribe_link: str = ""

    show_cta: bool = False
    cta_btn_link: str = ""
    cta_btn_text: str = ""

    text: str = NotImplemented


class BaseYamsaEmailService(BaseEmailService):
    FROM_EMAIL = "hello@yamsa.com"

    email_settings: YamsaEmailSettings = YamsaEmailSettings()
    email_context: YamsaEmailContext = YamsaEmailContext()

    template_name = "mail/email_text_base.html"

    def get_subject(self) -> str:
        return self.email_settings.SUBJECT_PREFIX + self.subject

    def get_context_data(self) -> dict:
        return {
            "context": {
                "subject": self.get_subject(),
                "greeting": self.get_greeting(),
                **self.get_email_settings().__dict__,
                **self.get_email_context().__dict__,
            }
        }

    def get_greeting(self):
        return self.email_settings.greeting_prefix + self.email_settings.greeting_suffix

    def get_email_settings(self):
        return self.email_settings

    def get_email_context(self):
        return self.email_context
