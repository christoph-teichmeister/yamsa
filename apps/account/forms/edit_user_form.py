from django.forms import ModelForm

from apps.account.models import User


class EditUserForm(ModelForm):
    class Meta:
        model = User
        fields = ("email", "paypal_me_username")
