from django import template
from django.template.defaulttags import url
from django.utils.safestring import mark_safe

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
