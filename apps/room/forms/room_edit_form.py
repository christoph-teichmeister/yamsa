from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room


class RoomEditForm(forms.ModelForm):
    """
    Form, which allows editing the name, description and preferred_currency of a room via the "normal" form in
    room-detail page and allows editing the status via the "close room" "reopen room" buttons in the room-detail page.
    """

    user: User = None

    class Meta:
        model = Room
        fields = ("name", "description", "preferred_currency", "status")

    def clean_status(self):
        new_status = self.cleaned_data["status"]
        old_status = self.instance.status

        if new_status != old_status and not self.instance.can_be_closed:
            raise ValidationError("This room still has open debts and can not be closed", code="invalid")

        return new_status

    def save(self, commit=True):
        if "status" in self.changed_data:
            handle_message(RoomStatusChanged(context_data={"room": self.instance}))

        # Set lastmodified fields
        self.instance.lastmodified_by = self.user
        self.instance.lastmodified_at = timezone.now()

        return super().save(commit)
