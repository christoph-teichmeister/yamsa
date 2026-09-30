from datetime import datetime
from decimal import Decimal

from django import template
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template.base import Parser, Token
from django.template.defaulttags import url
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timesince import timesince
from django.utils.translation import gettext as _

from apps.core.utils import format_number_with_thousands
from apps.room.room_seal import SEAL_ICON_LABELS, SEAL_ICONS

register = template.Library()


@register.filter
def room_seal_icon(room: dict):
    """`room` is the `current_room` context dict - see room_context()."""
    return room["resolved_seal_icon"]


@register.filter
def room_seal_tilt(room: dict):
    return room["seal_tilt"]


@register.simple_tag
def room_seal_icons():
    """The predefined seal icons a member can pick from, as (icon name, label) pairs.

    Not view context, so the picker works wherever the room sheet renders without every view
    having to thread it through.
    """
    return [(icon_name, SEAL_ICON_LABELS[icon_name]) for icon_name in SEAL_ICONS]


@register.simple_tag(takes_context=True)
def parse_user_text(context: template.Context, user_name: str, start_of_sentence: bool = False):
    request = context.get("request")

    if request.user.name == user_name:
        return format_html('<span class="me-involved">{}</span>', user_name)

    return format_html("<strong>{}</strong>", user_name)


@register.tag
def room_url(parser: Parser, token: Token):
    # The tag resolves against "current_room", which the room middleware only provides for URLs
    # carrying a room_slug. _side_menu_room_list.html renders outside such a URL and iterates a
    # room_qs instead, so it is the one template that binds "room".
    room_context_name = "current_room"

    if "_side_menu_room_list.html" in parser.origin.name:
        room_context_name = "room"

    token.contents += f" room_slug={room_context_name}.slug"

    return url(parser, token)


@register.filter
def room_status_label(status: int):
    """Render the label of a Room status value, for rows that are dicts rather than model instances."""
    from apps.room.models import Room

    return Room.status_label_for(status)


@register.filter
def room_last_used(value: datetime | None):
    """Say when a room was last used, in a single unit ("3 weeks ago").

    naturaltime and timesince both default to two units ("4 weeks, 2 days ago"), which costs
    the compact room row more width than the extra precision is worth on a phone. A paid_at in
    the future - the transaction form allows one - keeps naturaltime's wording, which already
    reads forwards.
    """
    if value is None:
        return ""

    if value > timezone.now():
        return naturaltime(value)

    # Same msgid the news cards and the transaction list already use, so no new string.
    return _("%(timesince)s ago") % {"timesince": timesince(value, depth=1)}


@register.filter
def format_with_thousands(value: object):
    """Formats a number with thousands separator using Django's locale-aware number_format.

    Uses django.utils.formats.number_format which respects i18n settings.

    Usage: {{ total_spent|format_with_thousands }}

    Examples:
    - de-DE: 1234.56 → 1.234,56
    - en-US: 1234.56 → 1,234.56
    - fr-FR: 1234.56 → 1 234,56
    """
    try:
        # Ensure value is numeric
        if isinstance(value, (int, float, Decimal)):
            numeric_value = value
        else:
            try:
                numeric_value = Decimal(str(value))
            except (ValueError, TypeError):
                return str(value)

        return format_number_with_thousands(numeric_value)
    except Exception:  # noqa: BLE001 - number formatting can fail in template-data-dependent ways; fall back to the raw value
        return str(value)
