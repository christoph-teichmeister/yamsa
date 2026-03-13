from dataclasses import dataclass

from django.utils.translation import gettext_lazy as _


@dataclass
class EmailBaseTextContext:
    SUBJECT_PREFIX: str = "yamsa | "

    header: str = "yamsa"
    # footer: str = "Your yamsa team"
    footer: str = ""
    sub_footer: str = _("yamsa | Yet another money split app")
    preheader_text: str = ""
    footer_disclaimer: str = ""
