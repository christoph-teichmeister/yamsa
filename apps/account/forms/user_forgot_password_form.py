from django import forms
from django.core.exceptions import ValidationError

from apps.account.models import User


class UserForgotPasswordForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)
        help_texts = {"email": "E-Mail your account is linked to"}

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not User.objects.filter(email=email).exists():
            raise ValidationError(f"The email address '{email}' is not registered with yamsa")

        return email
