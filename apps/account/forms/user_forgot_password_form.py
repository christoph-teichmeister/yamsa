from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.account.models import User


class UserForgotPasswordForm(forms.Form):
    class ExceptionMessage:
        UNKNOWN_EMAIL_ADDRESS = _("The email address '{email}' is not registered with yamsa")

    email = forms.EmailField(
        label=_("Email"),
        help_text=_("Email your account is linked to"),
    )

    class Meta:
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not User.objects.filter(email=email).exists():
            raise ValidationError(self.ExceptionMessage.UNKNOWN_EMAIL_ADDRESS.format(email=email))

        return email
