from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.room.models import Room


class RoomEditForm(forms.ModelForm):
    """Update a room's own metadata.

    The status is not in here: closing and reopening a room has consequences of its own — open
    debts, a confirmation, an event — and runs on its own cycle through RoomStatusForm.
    """

    user: User = None

    class Meta:
        model = Room
        fields = ("name", "description", "preferred_currency")
        # The model fields carry no verbose_name, so without these the sheet would label them in
        # English on a German page. Same pattern as EditUserForm.
        labels = {
            "name": _("Name"),
            "description": _("Description"),
            "preferred_currency": _("Preferred currency"),
        }

    def save(self, commit=True):
        self.instance.lastmodified_by = self.user
        self.instance.lastmodified_at = timezone.now()
        return super().save(commit)
