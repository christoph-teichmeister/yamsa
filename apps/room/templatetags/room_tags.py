from decimal import Decimal

from django import template
from django.template.defaulttags import url
from django.utils.safestring import mark_safe

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
