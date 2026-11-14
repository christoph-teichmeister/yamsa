from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _


@dataclass
class EmailExtraContext:
    show_unsubscribe: bool = False
    unsubscribe_link: str = ""
    unsubscribe_label: str = _("Unsubscribe")

    show_cta: bool = False
    cta_link: str = ""
    cta_label: str = ""
