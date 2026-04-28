from decimal import Decimal

from django import template
from django.template.defaulttags import url
from django.utils.safestring import mark_safe
from django.utils.formats import number_format

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
    # Templates using the room_url tag, will have "current_room" available in their context
    room_context_name = "current_room"

    # room/list.html does not and can not have current_room as context_variable, but it does iterate over a room_qs
    # calling each entry "room", so use that instead
    if "room/list.html" in parser.origin.name or "_side_menu_room_list.html" in parser.origin.name:
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

        # Use Django's built-in locale-aware formatting
        # With use_l10n=True and force_grouping=True, it respects the current locale
        formatted = number_format(
            numeric_value,
            decimal_pos=2,
            use_l10n=True,
            force_grouping=True
        )
        return mark_safe(formatted)
    except Exception:
        # Fallback: return original value if formatting fails
        return mark_safe(str(value))
