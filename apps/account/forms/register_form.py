from django.forms import ModelForm

from apps.account.models import User


class RegisterForm(ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "password")