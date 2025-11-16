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

    force_close = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput(attrs={"id": "force-close-flag"}),
    )

    user: User = None

    class Meta:
        model = Room
        fields = ("name", "description", "preferred_currency", "status")

    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get("status")
        old_status = self.instance.status
        force_close = cleaned_data.get("force_close")

        if new_status is None:
            return cleaned_data

        if (
            new_status != old_status
            and new_status == Room.StatusChoices.CLOSED
            and not self.instance.can_be_closed
            and not force_close
        ):
            msg = "This room still has open debts and can not be closed"
            raise ValidationError({"status": ValidationError(msg, code="invalid")})

        return cleaned_data

    def save(self, commit=True):
        new_status = self.cleaned_data.get("status")
        force_close = self.cleaned_data.get("force_close")

        if "status" in self.changed_data:
            if force_close and new_status == Room.StatusChoices.CLOSED:
                today = timezone.localdate()
                self.instance.debts.filter(settled=False).update(settled=True, settled_at=today)

            handle_message(RoomStatusChanged(context_data={"room": self.instance}))

        # Set lastmodified fields
        self.instance.lastmodified_by = self.user
        self.instance.lastmodified_at = timezone.now()

        return super().save(commit)
