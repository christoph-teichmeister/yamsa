from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.account.models import User


class GuestSendInvitationEmailForm(forms.ModelForm):
    class ExceptionMessage:
        EMAIL_ALREADY_EXISTS = _("User with email address '{email}' already exists")

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(self.ExceptionMessage.EMAIL_ALREADY_EXISTS.format(email=email))

        return email
