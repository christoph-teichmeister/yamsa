from django import forms
from django.core.exceptions import ValidationError

from apps.account.models import User


class UserForgotPasswordForm(forms.Form):
    class ExceptionMessage:
        UNKNOWN_EMAIL_ADDRESS = "The email address '{email}' is not registered with yamsa"

    email = forms.EmailField()

    class Meta:
        fields = ("email",)
        help_texts = {"email": "E-Mail your account is linked to"}

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not User.objects.filter(email=email).exists():
            raise ValidationError(self.ExceptionMessage.UNKNOWN_EMAIL_ADDRESS.format(email=email))

        return email
