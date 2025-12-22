"""Form helpers around editing users and validating profile uploads."""

from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _
from PIL import Image, UnidentifiedImageError

from apps.account.models import User
from apps.core.services import CompressPictureService

PROFILE_PICTURE_INVALID_IMAGE_ERROR = _("We could not read that file. Please upload a valid image.")


class EditUserForm(ModelForm):
    """Handle user edits while validating uploaded avatars."""

    class Meta:
        model = User
        fields = (
            "name",
            "email",
            "profile_picture",
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
        """Compress an uploaded profile picture prior to saving the user."""

        picture = self.cleaned_data.get("profile_picture")
        if picture:
            compressed_picture = CompressPictureService(picture).process()
            self.cleaned_data["profile_picture"] = compressed_picture
            self.instance.profile_picture = compressed_picture

        # Remove stored webpush subscriptions when the user explicitly opts out.
        if self.cleaned_data["wants_to_receive_webpush_notifications"] is False:
            self.instance.webpush_infos.all().delete()

        return super().save(commit)

    def clean_profile_picture(self):
        """Ensure the uploaded file is a valid image before accepting it."""
        picture = self.cleaned_data.get("profile_picture")
        if not picture:
            return picture

        try:
            with Image.open(picture) as image:
                image.verify()
        except (UnidentifiedImageError, OSError) as exc:
            raise ValidationError(PROFILE_PICTURE_INVALID_IMAGE_ERROR) from exc

        picture.seek(0)
        return picture
