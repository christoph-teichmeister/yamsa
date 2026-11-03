import json

from django import template
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

_json_script_escapes = {
    ord(">"): "\\u003E",
    ord("<"): "\\u003C",
    ord("&"): "\\u0026",
}


@register.simple_tag(takes_context=True)
def json_script_nonce(context: template.Context, value: object, element_id: str) -> str:
    """Like Django's json_script filter, but injects the CSP nonce from context."""
    json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
    nonce = context.get("csp_nonce", "")
    return format_html(
        '<script id="{}" type="application/json" nonce="{}">{}</script>',
        element_id,
        nonce,
        mark_safe(json_str),  # noqa: S308 - mirrors Django's own json_script: JSON is escaped for <script> context above
    )


@register.filter
def get_item(dictionary: dict, key: object) -> object | None:
    """Look up a dict value by key in templates: {{ my_dict|get_item:some_var }}."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.inclusion_tag("shared_partials/_former_member_tag.html", takes_context=True)
def former_member_tag(context: template.Context, user_id: int | None) -> dict[str, bool]:
    """Chip next to a name whose user has left the room but still appears in its history.

    The member ids are read once per request, because a list prints this tag on every row.
    """
    request = context.get("request")
    room = getattr(request, "room", None)
    if room is None or user_id is None:
        return {"is_former_member": False}
    if not hasattr(request, "_room_member_ids"):
        request._room_member_ids = set(room.users.values_list("id", flat=True))
    return {"is_former_member": user_id not in request._room_member_ids}
