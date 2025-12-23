import emoji as emoji_lib
from django import forms
from django.core.validators import RegexValidator
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


class RoomCategoryCreateForm(forms.Form):
    name = forms.CharField(max_length=100)
    emoji = forms.CharField(max_length=10, validators=[validate_single_emoji])
    color = forms.CharField(
        max_length=7,
        required=False,
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", message=_("Enter a color in #RRGGBB format."))],
    )
    order_index = forms.IntegerField(min_value=0, required=False)
    make_default = forms.BooleanField(required=False)


class RoomCategoryUpdateForm(forms.Form):
    room_category_id = forms.IntegerField(widget=forms.HiddenInput)
    order_index = forms.IntegerField(min_value=0)
    make_default = forms.BooleanField(required=False)
