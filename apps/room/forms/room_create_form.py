from django import forms
from django.utils.translation import gettext_lazy as _

from apps.room.models import Room


class RoomCreateForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ("name", "preferred_currency", "description")
        # The model fields carry no verbose_name, so without these the form would label them
        # in English on a German page. Same pattern as EditUserForm and RoomEditForm.
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "preferred_currency": _("Preferred currency"),
        }
