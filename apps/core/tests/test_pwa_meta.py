from django.conf import settings
from django.template.loader import render_to_string


class TestPwaMeta:
    def test_manifest_is_standalone_and_icons_are_not_maskable(self) -> None:
        assert settings.MANIFEST["display"] == "standalone"
        assert "fullscreen" not in settings.MANIFEST["display_override"]
        assert all(icon.get("purpose", "any") == "any" for icon in settings.MANIFEST["icons"])

    def test_only_one_apple_touch_icon_is_emitted(self) -> None:
        html = render_to_string("core/pwa/load_meta_data.html", {"manifest": settings.MANIFEST})

        assert html.count('rel="apple-touch-icon"') == 1
        assert 'sizes="180x180"' in html
        assert html.count('name="theme-color"') == 2
