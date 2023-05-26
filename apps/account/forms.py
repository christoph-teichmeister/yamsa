from django.forms import ModelForm

from apps.account.models import User


class LoginForm(ModelForm):
    class Meta:
        model = User
        fields = ("username", "password")


class RegisterForm(ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "password")


class EditUserForm(ModelForm):
    class Meta:
        model = User
        fields = ("email", "paypal_me_link")
