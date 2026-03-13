from django import forms
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

from .validators import validate_single_emoji


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
