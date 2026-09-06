"""Form helpers around editing users."""

from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from apps.account.models import User


class EditUserForm(ModelForm):
    """Handle user edits.

    The profile picture is deliberately not a field here: it has its own upload and delete cycle
    (see ProfilePictureForm), so saving the profile never touches it.
    """

    class Meta:
        model = User
        fields = (
            "name",
            "email",
            "paypal_me_username",
            "language",
            "wants_to_receive_webpush_notifications",
            "wants_to_receive_payment_reminders",
            "wants_to_receive_room_reminders",
        )
        labels = {
            "wants_to_receive_webpush_notifications": _("Receive push notifications"),
            "language": _("Preferred language"),
            "wants_to_receive_payment_reminders": _("Receive payment reminder emails"),
            "wants_to_receive_room_reminders": _("Receive room reminder emails"),
        }

    def save(self, commit=True):
        # Remove stored webpush subscriptions when the user explicitly opts out.
        if self.cleaned_data["wants_to_receive_webpush_notifications"] is False:
            self.instance.webpush_infos.all().delete()

        return super().save(commit)
