from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.account.models import User
from apps.room.models import Room


class RoomStatusForm(forms.ModelForm):
    """Flip a room open ↔ closed.

    The status runs on its own cycle, so this form owns exactly the two fields that cycle needs.
    htmx posts the enclosing sheet's fields along with the request; keeping the field list this
    narrow means every one of them is ignored by construction rather than by a filter.
    """

    class ExceptionMessage:
        HAS_OPEN_DEBTS = _("This room still has open debts and can not be closed")

    # Set by the dialog that asks whether to close a room with debts on it.
    force_close = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput())

    user: User = None

    class Meta:
        model = Room
        fields = ("status",)

    @property
    def closes_the_room(self) -> bool:
        """Whether this post is the transition to closed, rather than any save on a closed room."""

        return "status" in self.changed_data and self.cleaned_data.get("status") == Room.StatusChoices.CLOSED

    def clean(self):
        cleaned_data = super().clean()
        new_status = cleaned_data.get("status")

        if new_status is None:
            return cleaned_data

        # clean() runs before the instance is updated, so this still reads the stored status.
        closing = new_status != self.instance.status and new_status == Room.StatusChoices.CLOSED
        if closing and not self.instance.can_be_closed and not cleaned_data.get("force_close"):
            raise ValidationError({"status": ValidationError(self.ExceptionMessage.HAS_OPEN_DEBTS, code="invalid")})

        return cleaned_data

    def save(self, commit=True):
        self.instance.lastmodified_by = self.user
        self.instance.lastmodified_at = timezone.now()
        return super().save(commit)
