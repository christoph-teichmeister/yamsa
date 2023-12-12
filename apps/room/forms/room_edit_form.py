from django import forms
from django.core.exceptions import ValidationError

from apps.room.models import Room


class RoomEditForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ("name", "description", "preferred_currency", "status")

    def clean_status(self):
        new_status = self.cleaned_data["status"]
        old_status = self.instance.status

        if new_status != old_status and not self.instance.can_be_closed:
            raise ValidationError("This room still has open debts and can not be closed", code="invalid")

        return new_status
