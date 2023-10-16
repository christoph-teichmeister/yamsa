from django import forms

from apps.room.models import Room


class RoomCreateForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ("name", "preferred_currency", "description")
