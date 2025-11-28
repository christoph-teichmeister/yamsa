from django import forms
from django.utils.translation import gettext_lazy as _

from apps.account.forms.utils import validate_unique_email
from apps.account.models import User


class GuestSendInvitationEmailForm(forms.ModelForm):
    class ExceptionMessage:
        EMAIL_ALREADY_EXISTS = _("User with email address '{email}' already exists")

    class Meta:
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"]
        normalized_email = validate_unique_email(email, error_message=self.ExceptionMessage.EMAIL_ALREADY_EXISTS)

        self.cleaned_data["email"] = normalized_email
        return normalized_email
