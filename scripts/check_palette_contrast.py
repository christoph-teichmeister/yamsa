"""Hold the palette in apps/static_src/tailwind.css to its contrast and hue promises.

The values in that file are not a matter of taste: a text token has to reach 4.5:1 on every
ground it is used on, a control border and the focus ring 3:1, and the neutrals of both themes
have to sit on one hue so a cold brand never lands on a warm ground. This script is what makes
those promises checkable - run it after touching a colour.
"""

from __future__ import annotations

import argparse
import colorsys
import re
import sys
from pathlib import Path

CSS_PATH = Path(__file__).resolve().parent.parent / "apps" / "static_src" / "tailwind.css"

BODY_TEXT_RATIO = 4.5
NON_TEXT_RATIO = 3.0
MAX_HUE_SPREAD = 20

TEXT_TOKENS = (
    "ink",
    "ink-muted",
    "ink-subtle",
    "brand-text",
    "link",
    "success-text",
    "warning-text",
    "danger-text",
)
# Every opaque ground text can end up on, not just the common ones: a tertiary label on a hovered
# row or a raised card is the same reading task as one on a card.
GROUNDS = ("surface", "surface-raised", "surface-sunken", "surface-hover", "canvas")
# The `-soft` tints are translucent, so what a badge label really sits on is the tint composited
# over whatever carries the badge.
TINTED = ("brand", "success", "warning", "danger")
NEUTRALS = ("canvas", "surface-sunken", "line")

BLOCK_PATTERN = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}", re.MULTILINE)
DECLARATION_PATTERN = re.compile(r"--yamsa-([a-z-]+):\s*([^;]+);")
COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)


def _channels(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if value.startswith("#"):
        digits = value.lstrip("#")
        return tuple(int(digits[i : i + 2], 16) for i in (0, 2, 4))
    numbers = [int(part) for part in re.findall(r"\d+", value)[:3]]
    return tuple(numbers)


def _alpha(value: str) -> float:
    """The alpha of `rgb(r g b / .14)` or `rgb(var(--…), 0.12)`; 1 when the colour is opaque."""
    match = re.search(r"[,/]\s*(0?\.\d+|1(?:\.0+)?)\s*\)\s*$", value.strip())
    return float(match.group(1)) if match else 1.0


def flatten(color: str, ground: str) -> str:
    """What the eye actually sees when a translucent colour is painted on an opaque one."""
    alpha = _alpha(color)
    if alpha >= 1:
        return color
    top, bottom = _channels(color), _channels(ground)
    mixed = (round(top[index] * alpha + bottom[index] * (1 - alpha)) for index in range(3))
    return "#" + "".join(f"{channel:02x}" for channel in mixed)


def _relative_luminance(color: str) -> float:
    def channel(value: int) -> float:
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(part) for part in _channels(color))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(first: str, second: str) -> float:
    a, b = _relative_luminance(first), _relative_luminance(second)
    lighter, darker = max(a, b), min(a, b)
    return (lighter + 0.05) / (darker + 0.05)


def hue(color: str) -> int:
    red, green, blue = (part / 255 for part in _channels(color))
    return round(colorsys.rgb_to_hls(red, green, blue)[0] * 360)


def read_themes(css: str) -> dict[str, dict[str, str]]:
    """Resolve the `--yamsa-*` tokens per theme, following the `rgb(var(--…-rgb))` indirection."""
    themes: dict[str, dict[str, str]] = {"light": {}, "dark": {}}
    shared: dict[str, str] = {}

    for match in BLOCK_PATTERN.finditer(COMMENT_PATTERN.sub("", css)):
        # Everything up to the last statement is an at-rule that happens to precede this block -
        # `@custom-variant dark ([data-bs-theme="dark"] &);` would otherwise read as the selector.
        selector = match.group("selector").split(";")[-1]
        declarations = dict(DECLARATION_PATTERN.findall(match.group("body")))
        if not declarations:
            continue
        if 'data-bs-theme="dark"' in selector:
            themes["dark"].update(declarations)
        elif 'data-bs-theme="light"' in selector:
            themes["light"].update(declarations)
        elif ":root" in selector:
            shared.update(declarations)

    for theme in themes.values():
        for name, value in shared.items():
            theme.setdefault(name, value)
        for name, value in list(theme.items()):
            reference = re.fullmatch(r"rgb\(var\(--yamsa-([a-z-]+)\)\)", value.strip())
            if reference:
                theme[name] = theme[reference.group(1)]
            # `rgb(var(--yamsa-brand-rgb), 0.12)` keeps its alpha but needs the triplet inlined.
            tinted = re.fullmatch(r"rgb\(var\(--yamsa-([a-z-]+)\),\s*([\d.]+)\)", value.strip())
            if tinted:
                red, green, blue = _channels(theme[tinted.group(1)])
                theme[name] = f"rgb({red} {green} {blue} / {tinted.group(2)})"
    return themes


def failures(themes: dict[str, dict[str, str]]) -> list[str]:
    found: list[str] = []
    for name, tokens in themes.items():
        for ground in GROUNDS:
            for token in TEXT_TOKENS:
                ratio = contrast(tokens[token], tokens[ground])
                if ratio < BODY_TEXT_RATIO:
                    found.append(f"{name}: {token} on {ground} is {ratio:.2f}:1, needs {BODY_TEXT_RATIO}:1")

        for tint_name in TINTED:
            for ground in GROUNDS:
                tint = flatten(tokens[f"{tint_name}-soft"], tokens[ground])
                ratio = contrast(tokens[f"{tint_name}-text"], tint)
                if ratio < BODY_TEXT_RATIO:
                    found.append(
                        f"{name}: {tint_name}-text on {tint_name}-soft over {ground} ({tint}) is "
                        f"{ratio:.2f}:1, needs {BODY_TEXT_RATIO}:1"
                    )

        checks = (
            ("on-brand", "brand", BODY_TEXT_RATIO, "a button label on the brand fill"),
            ("on-brand", "brand-hover", BODY_TEXT_RATIO, "a button label on the hovered brand fill"),
            ("brand", "surface", NON_TEXT_RATIO, "the focus ring on a surface"),
            ("line-strong", "surface", NON_TEXT_RATIO, "a control border on a surface"),
        )
        for first, second, needed, label in checks:
            ratio = contrast(tokens[first], tokens[second])
            if ratio < needed:
                found.append(f"{name}: {label} is {ratio:.2f}:1, needs {needed}:1")

        hues = {token: hue(tokens[token]) for token in NEUTRALS}
        spread = max(hues.values()) - min(hues.values())
        if spread > MAX_HUE_SPREAD:
            found.append(f"{name}: the neutrals span {spread}° of hue ({hues}), at most {MAX_HUE_SPREAD}°")

    light = sum(hue(themes["light"][token]) for token in NEUTRALS) / len(NEUTRALS)
    dark = sum(hue(themes["dark"][token]) for token in NEUTRALS) / len(NEUTRALS)
    if abs(light - dark) > MAX_HUE_SPREAD:
        found.append(f"the two themes sit {abs(light - dark):.0f}° apart in hue, at most {MAX_HUE_SPREAD}°")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="print every measured ratio")
    arguments = parser.parse_args()

    themes = read_themes(CSS_PATH.read_text())

    if arguments.verbose:
        for name, tokens in themes.items():
            print(f"[{name}]")
            for ground in GROUNDS:
                for token in TEXT_TOKENS:
                    print(f"  {token:14} on {ground:15} {contrast(tokens[token], tokens[ground]):5.2f}:1")

    found = failures(themes)
    for failure in found:
        print(f"FAIL {failure}")
    if found:
        print(f"\n{len(found)} palette check(s) failed in {CSS_PATH}.")
        return 1
    print(f"Palette in {CSS_PATH.name} passes every contrast and hue check.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
