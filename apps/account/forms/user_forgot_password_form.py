from django import forms
from django.utils.translation import gettext_lazy as _


class UserForgotPasswordForm(forms.Form):
    email = forms.EmailField(
        label=_("Email"),
        help_text=_("Email your account is linked to"),
    )

    class Meta:
        fields = ("email",)
