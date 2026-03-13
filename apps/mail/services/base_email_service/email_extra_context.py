from dataclasses import dataclass


@dataclass
class EmailExtraContext:
    show_unsubscribe: bool = False
    unsubscribe_link: str = ""

    show_cta: bool = False
    cta_link: str = ""
    cta_label: str = ""
