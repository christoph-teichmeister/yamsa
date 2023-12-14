from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.account.models import User
from apps.core.event_loop.runner import handle_message
from apps.room.messages.events.room_status_changed import RoomStatusChanged
from apps.room.models import Room
from apps.webpush.dataclasses import Notification


class RoomEditForm(forms.ModelForm):
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
        # Notify users when a room is closed
        if self.instance.status == self.instance.StatusChoices.CLOSED:
            notification = Notification(
                payload=Notification.Payload(
                    head="Room closed",
                    body=f'{self.user.name} closed "{self.instance.name}"',
                ),
            )
            for user in self.instance.room_users.exclude(id=self.user.id):
                notification.payload.click_url = reverse("room-dashboard", kwargs={"room_slug": self.instance.slug})
                notification.send_to_user(user)

        # Notify users when a room is reopened
        if self.instance.status == self.instance.StatusChoices.OPEN:
            notification = Notification(
                payload=Notification.Payload(
                    head="Room re-opened",
                    body=f'{self.user.name} opened "{self.instance.name}"',
                ),
            )
            for user in self.instance.room_users.exclude(id=self.user.id):
                notification.payload.click_url = reverse("room-dashboard", kwargs={"room_slug": self.instance.slug})
                notification.send_to_user(user)

        if "status" in self.changed_data:
            handle_message(RoomStatusChanged(context_data={"room": self.instance}))

        # Set lastmodified fields
        self.instance.lastmodified_by = self.user
        self.instance.lastmodified_at = timezone.now()

        return super().save(commit)
