from django import forms
from django.utils.translation import gettext_lazy as _


class LoginForm(forms.Form):
    """Validation only - account/login.html renders the fields itself."""

    email = forms.EmailField(label=_("Email address"))
    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput)
    remember_me = forms.BooleanField(label=_("Stay signed in for longer"), required=False)
