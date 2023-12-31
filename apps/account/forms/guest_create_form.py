from django import forms

from apps.account.models import User


class GuestCreateForm(forms.ModelForm):
    room_slug = forms.CharField()

    class Meta:
        model = User
        fields = ("name", "room_slug")
