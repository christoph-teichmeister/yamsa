from django import forms
from django.contrib.auth import hashers
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from apps.account.models import User


class RegisterForm(ModelForm):
    id = forms.IntegerField(required=False)

    class Meta:
        model = User
        fields = ("id", "is_guest", "username", "email", "password")

    def save(self, commit=True):
        self.instance.id = self.cleaned_data["id"]
        self.instance.name = self.cleaned_data["username"]
        return super().save(commit)

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(f"The email address '{email}' is already in use")

        return email

    def clean_password(self):
        return hashers.make_password(self.cleaned_data["password"])
