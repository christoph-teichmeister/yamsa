from django import forms
from django.contrib.auth import authenticate, hashers
from django.core.exceptions import ValidationError

from apps.account.models import User


class ChangePasswordForm(forms.ModelForm):
    class ExceptionMessage:
        PASSWORD_INCORRECT = "Your current password is incorrect"
        PASSWORDS_DO_NOT_MATCH = "Passwords do not match"

    old_password = forms.CharField(required=True, label="Your current password")
    new_password = forms.CharField(required=True, label="Your new password")
    new_password_confirmation = forms.CharField(required=True, label="Confirm your new password")

    class Meta:
        model = User
        fields = ("id", "old_password", "new_password", "new_password_confirmation")

    def clean_old_password(self):
        possible_user = authenticate(email=self.instance.email, password=self.cleaned_data["old_password"])
        if possible_user is None:
            raise ValidationError(self.ExceptionMessage.PASSWORD_INCORRECT)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["new_password"] != cleaned_data["new_password_confirmation"]:
            raise ValidationError({"new_password_confirmation": self.ExceptionMessage.PASSWORDS_DO_NOT_MATCH})

    def save(self, commit=True):
        self.instance.password = hashers.make_password(self.cleaned_data["new_password"])
        return super().save(commit)
