from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _

from apps.account.models import User


@dataclass
class EmailUserTextContext:
    greeting_prefix: str = _("Hey")
    greeting_suffix: str = "👋"

    user: User = None
    text_list: list[str] = NotImplemented
