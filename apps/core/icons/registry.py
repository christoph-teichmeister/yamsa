"""The icon sprite: which icons go into it, and how it is built.

Icons are bootstrap-icons SVGs, but the font is not shipped - 2078 glyphs and a
97 KB stylesheet to draw the 72 the app actually uses. `sync_icons` collects the
used names, writes them into one sprite, and the `icon` tag points a `<use>` at
it. The npm package stays a devDependency: it is the source the sprite is built
from, never something a request touches.
"""

import re
from pathlib import Path

from django.conf import settings

ICON_SOURCE_DIR = Path(settings.BASE_DIR) / "node_modules" / "bootstrap-icons" / "icons"
SPRITE_PATH = Path(settings.APPS_DIR) / "static" / "icons" / "sprite.svg"

# `{% icon "chevron-down" %}` — the literal names, which is nearly all of them.
_TAG_CALL = re.compile(r"""\{%\s*icon\s+["']([a-z0-9-]+)["']""")

# A name that reaches the tag through a variable cannot be found by reading the
# templates. Every one of them is a literal somewhere in Python or in an
# `{% include %}`, so this is the list of those places' values.
NAMES_PASSED_AS_VARIABLES = frozenset(
    {
        # apps/room/services/dashboard_tab_service.py
        "wallet",
        "piggy-bank",
        "people",
        "gear",
        # shared_partials/member_form.html, via its callers
        "at",
        "send-check",
        "person-plus",
        "check-lg",
        # account/partials/_people_action.html, via its callers
        "person-check",
        "x-octagon",
        "eye-slash",
        "arrow-up-right",
    }
)


def collect_icon_names(template_root: Path) -> set[str]:
    """Every icon the sprite has to carry, read off the templates plus the list above."""
    names = set(NAMES_PASSED_AS_VARIABLES)
    for template in template_root.rglob("*.html"):
        names.update(_TAG_CALL.findall(template.read_text(encoding="utf-8")))
    return names


def sprite_symbol_names(sprite: str) -> set[str]:
    """The icons a built sprite carries, read back out of it."""
    return set(re.findall(r'<symbol id="([^"]+)"', sprite))


def build_sprite(names: set[str], source_dir: Path = ICON_SOURCE_DIR) -> str:
    """One <symbol> per icon, in a stable order so the file only changes when the icons do."""
    symbols = []
    for name in sorted(names):
        source = source_dir / f"{name}.svg"
        if not source.exists():
            message = f"bootstrap-icons has no icon named {name!r} ({source})"
            raise FileNotFoundError(message)

        svg = source.read_text(encoding="utf-8")
        view_box = re.search(r'viewBox="([^"]+)"', svg)
        if not view_box:
            message = f"{source} has no viewBox"
            raise ValueError(message)

        # Everything between the root tags. The root's own width/height/class are
        # dropped: the size comes from the `.bi` rule at the use site.
        body = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", svg, flags=re.S).strip()
        symbols.append(f'<symbol id="{name}" viewBox="{view_box.group(1)}" fill="currentColor">{body}</symbol>')

    joined = "\n".join(symbols)
    return f'<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n{joined}\n</svg>\n'
