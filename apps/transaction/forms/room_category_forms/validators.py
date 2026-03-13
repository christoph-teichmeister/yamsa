import emoji as emoji_lib
from django import forms
from django.utils.translation import gettext_lazy as _


def validate_single_emoji(value: str) -> None:
    trimmed = value.strip()
    if not trimmed:
        raise forms.ValidationError(_("Enter a single emoji character."))

    matches = emoji_lib.emoji_list(trimmed)
    if len(matches) != 1:
        raise forms.ValidationError(_("Enter a single emoji character."))

    match = matches[0]
    match_start = match.get("match_start")
    match_end = match.get("match_end")
    if match_start != 0 or match_end != len(trimmed):
        raise forms.ValidationError(_("Enter a single emoji character."))
