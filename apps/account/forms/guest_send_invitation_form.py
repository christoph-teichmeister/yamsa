from django import forms
from django.core.exceptions import ValidationError

from apps.account.models import User


class GuestSendInvitationEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(f"User with email address '{email}' already exists")

        return email
