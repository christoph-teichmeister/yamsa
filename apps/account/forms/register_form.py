from django.contrib.auth import hashers
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from apps.account.forms.utils import validate_unique_email
from apps.account.models import User


class RegisterForm(ModelForm):
    class ExceptionMessage:
        EMAIL_ADDRESS_ALREADY_IN_USE = _("The email address '{email}' is already in use")

    class Meta:
        model = User
        fields = ("is_guest", "name", "email", "password")

    def clean_email(self) -> str:
        email = self.cleaned_data["email"]
        normalized_email = validate_unique_email(
            email,
            error_message=self.ExceptionMessage.EMAIL_ADDRESS_ALREADY_IN_USE,
            exclude_user_id=self.instance.id,
        )

        self.cleaned_data["email"] = normalized_email
        return normalized_email

    def clean_password(self) -> str:
        return hashers.make_password(self.cleaned_data["password"])

    def save(self, commit: bool = True) -> User:
        self.instance.name = self.cleaned_data["name"]
        return super().save(commit)
