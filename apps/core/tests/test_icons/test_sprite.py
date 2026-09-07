import re
from pathlib import Path

from apps.core.icons import SPRITE_PATH, collect_icon_names, sprite_symbol_names


class TestSprite:
    def test_it_carries_exactly_the_icons_in_use(self, settings):
        """Names only, like `sync_icons --check`: neither this nor CI has node_modules."""
        used = collect_icon_names(Path(settings.APPS_DIR))
        in_sprite = sprite_symbol_names(SPRITE_PATH.read_text(encoding="utf-8"))

        assert used - in_sprite == set(), "used but missing from the sprite"
        assert in_sprite - used == set(), "in the sprite but no longer used"

    def test_every_symbol_is_addressable_and_scalable(self):
        sprite = SPRITE_PATH.read_text(encoding="utf-8")
        symbols = re.findall(r'<symbol id="([^"]+)" viewBox="([^"]+)"', sprite)

        assert symbols, "the sprite carries no symbols"
        assert len({name for name, _ in symbols}) == len(symbols), "duplicate symbol ids"
        # Without a viewBox a <use> renders at the sprite's size, not the call site's.
        assert all(view_box.count(" ") == 3 for _, view_box in symbols)
