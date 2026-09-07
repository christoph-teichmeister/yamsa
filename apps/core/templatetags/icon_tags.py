from django import template
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.html import format_html

register = template.Library()


@register.simple_tag
def icon(name, css_class=""):
    """Render one icon out of the sprite.

        {% icon "chevron-down" %}
        {% icon "trash" "text-danger-text" %}

    The `.bi` class carries the sizing, so an icon is 1em of the text around it and
    takes its colour from `currentColor` - the same contract the icon font had, which
    is why the call sites keep whatever `text-*` utilities they already had.

    `name` is a bootstrap-icons name without the `bi-` prefix. A name that is not in
    the sprite renders an empty box rather than raising: an icon is decoration, and a
    view is not worth a 500 over one. `sync_icons --check` is what catches it, in CI.
    """
    classes = f"bi {css_class}".strip()
    return format_html(
        '<svg class="{}" aria-hidden="true" focusable="false"><use href="{}#{}"></use></svg>',
        classes,
        staticfiles_storage.url("icons/sprite.svg"),
        name,
    )
