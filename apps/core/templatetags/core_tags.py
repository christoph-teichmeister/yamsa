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
def json_script_nonce(context, value, element_id):
    """Like Django's json_script filter, but injects the CSP nonce from context."""
    json_str = json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
    nonce = context.get("csp_nonce", "")
    return format_html(
        '<script id="{}" type="application/json" nonce="{}">{}</script>',
        element_id,
        nonce,
        mark_safe(json_str),
    )
