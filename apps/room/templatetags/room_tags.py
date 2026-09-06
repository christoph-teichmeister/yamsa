from decimal import Decimal

from django import template
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.template.defaulttags import url
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from django.utils.translation import gettext as _

from apps.core.utils import format_number_with_thousands

register = template.Library()


@register.simple_tag(takes_context=True)
def parse_user_text(context, user_name: str, start_of_sentence: bool = False):
    request = context.get("request")

    if request.user.name == user_name:
        user_text = f'<span class="me-involved">{user_name}</span>'
    else:
        user_text = f"<strong>{user_name}</strong>"

    return mark_safe(user_text)


@register.tag
def room_url(parser, token):
    # The tag resolves against "current_room", which the room middleware only provides for URLs
    # carrying a room_slug. _side_menu_room_list.html renders outside such a URL and iterates a
    # room_qs instead, so it is the one template that binds "room".
    room_context_name = "current_room"

    if "_side_menu_room_list.html" in parser.origin.name:
        room_context_name = "room"

    token.contents += f" room_slug={room_context_name}.slug"

    return url(parser, token)


@register.filter
def room_status_label(status):
    """Render the label of a Room status value, for rows that are dicts rather than model instances."""
    from apps.room.models import Room

    return Room.status_label_for(status)


@register.filter
def room_last_used(value):
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
def format_with_thousands(value):
    """
    Formats a number with thousands separator using Django's locale-aware number_format.

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
                return mark_safe(str(value))

        return mark_safe(format_number_with_thousands(numeric_value))
    except Exception:
        # Fallback: return original value if formatting fails
        return mark_safe(str(value))
