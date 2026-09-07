import pytest

from apps.core.icons import build_sprite

CHEVRON = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" '
    'class="bi bi-chevron-down" viewBox="0 0 16 16">\n  <path d="M1 4h14"/>\n</svg>'
)


@pytest.fixture
def source_dir(tmp_path):
    """Stands in for node_modules/bootstrap-icons/icons, which CI does not install."""
    (tmp_path / "chevron-down.svg").write_text(CHEVRON, encoding="utf-8")
    (tmp_path / "trash.svg").write_text(CHEVRON.replace("chevron-down", "trash"), encoding="utf-8")
    return tmp_path


class TestBuildSprite:
    def test_it_keeps_the_drawing_and_drops_the_wrapper(self, source_dir):
        sprite = build_sprite({"chevron-down"}, source_dir)

        assert '<symbol id="chevron-down" viewBox="0 0 16 16" fill="currentColor">' in sprite
        assert '<path d="M1 4h14"/>' in sprite
        # The root's own size would pin every icon to 16px and defeat the 1em contract.
        assert 'width="16"' not in sprite
        assert sprite.count("<svg") == 1

    def test_symbols_are_ordered_by_name(self, source_dir):
        """A set has no order; without sorting the file would churn on every run."""
        sprite = build_sprite({"trash", "chevron-down"}, source_dir)

        assert sprite.index('id="chevron-down"') < sprite.index('id="trash"')

    def test_an_unknown_icon_is_named_in_the_error(self, source_dir):
        with pytest.raises(FileNotFoundError, match="no-such-icon"):
            build_sprite({"no-such-icon"}, source_dir)

    def test_an_svg_without_a_viewbox_is_rejected(self, source_dir, tmp_path):
        (tmp_path / "broken.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")

        # Without a viewBox a <use> renders at the sprite's size, so this must not slip through.
        with pytest.raises(ValueError, match="viewBox"):
            build_sprite({"broken"}, source_dir)
