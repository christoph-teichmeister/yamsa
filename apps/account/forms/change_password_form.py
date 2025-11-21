from django import forms
from django.contrib.auth import authenticate, hashers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.account.models import User


class ChangePasswordForm(forms.ModelForm):
    class ExceptionMessage:
        PASSWORD_INCORRECT = _("Your current password is incorrect")
        PASSWORDS_DO_NOT_MATCH = _("Passwords do not match")

    _request = None  # set by .__init__()

    old_password = forms.CharField(required=True, label=_("Your current password"))
    new_password = forms.CharField(required=True, label=_("Your new password"))
    new_password_confirmation = forms.CharField(required=True, label=_("Confirm your new password"))

    class Meta:
        model = User
        fields = ("id", "old_password", "new_password", "new_password_confirmation")

    def __init__(self, *args, **kwargs):
        self._request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        possible_user = authenticate(
            request=self._request, email=self.instance.email, password=self.cleaned_data["old_password"]
        )
        if possible_user is None:
            raise ValidationError(self.ExceptionMessage.PASSWORD_INCORRECT)

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data["new_password"] != cleaned_data["new_password_confirmation"]:
            raise ValidationError({"new_password_confirmation": self.ExceptionMessage.PASSWORDS_DO_NOT_MATCH})

    def save(self, commit=True):
        self.instance.password = hashers.make_password(self.cleaned_data["new_password"])
        return super().save(commit)
