from django import template
from django.template.defaulttags import url

register = template.Library()


@register.simple_tag(takes_context=True)
def parse_user_text(context, user_name: str, start_of_sentence: bool = False):
    request = context.get("request")

    if request.user.name == user_name:
        you = "you" if not start_of_sentence else "You"
        user_text = f'<span class="me-involved">{you}</span>'
    else:
        user_text = f"<strong>{user_name}</strong>"

    return user_text


@register.tag
def room_url(parser, token):
    # Templates using the room_url tag, will have "current_room" available in their context
    room_context_name = "current_room"

    # room/list.html does not and can not have current_room as context_variable, but it does iterate over a room_qs
    # calling each entry "room", so use that instead
    if "room/list.html" in parser.origin.name:
        room_context_name = "room"

    token.contents += f" room_slug={room_context_name}.slug"

    return url(parser, token)
