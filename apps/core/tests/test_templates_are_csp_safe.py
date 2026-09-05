import re
from pathlib import Path

from bs4 import BeautifulSoup
from django.conf import settings

APPS_DIR = Path(settings.BASE_DIR) / "apps"

# htmx compiles both of these with new Function(): the trigger filter in `hx-trigger="keyup[...]"`
# and the body of any `hx-on:` attribute. The project's CSP serves script-src without
# 'unsafe-eval', so the browser refuses to run them - and htmx then fires the trigger anyway, on
# every key. Keyboard activation belongs in the nonce'd bundle instead
# (apps/static/js/navigation.js, `data-keyboard-click`).
HX_TRIGGER_FILTER = re.compile(r"hx-trigger=\"[^\"]*\[")
HX_ON_ATTRIBUTE = re.compile(r"hx-on:")


class TestTemplatesAreCspSafe:
    def _template_paths(self) -> list[Path]:
        paths = sorted(APPS_DIR.glob("**/templates/**/*.html"))
        assert paths, "No templates found - the glob is wrong, not the templates"
        return paths

    def test_no_template_relies_on_htmx_evaluating_a_string(self):
        offenders = []
        for path in self._template_paths():
            content = path.read_text()
            for pattern in (HX_TRIGGER_FILTER, HX_ON_ATTRIBUTE):
                if pattern.search(content):
                    offenders.append(f"{path.relative_to(APPS_DIR)}: {pattern.pattern}")

        assert offenders == [], "These templates need new Function(), which the CSP blocks: " + ", ".join(offenders)

    def test_every_scripted_button_role_is_keyboard_activatable(self):
        # role="button" promises Enter/Space. On a native control the browser delivers that; on
        # anything else it only works if the delegated handler in navigation.js can see the
        # element, which it does by the data-keyboard-click marker.
        native_controls = {"a", "button", "input", "summary"}
        offenders = []
        for path in self._template_paths():
            soup = BeautifulSoup(path.read_text(), "html.parser")
            for element in soup.select('[role="button"]'):
                if element.name in native_controls:
                    continue
                if "data-keyboard-click" in element.attrs:
                    continue
                offenders.append(f"{path.relative_to(APPS_DIR)}: <{element.name}>")

        assert offenders == [], 'role="button" on a non-native element without data-keyboard-click: ' + ", ".join(
            offenders
        )
